// End-to-end over real loopback sockets: RoomHost + RelayHostBridge on the host device,
// a joining device through make_relay_transport, and tools/room_relay.py in between.
// Run by tests/test_relay_link.py, which starts the relay with fake tickets.
#include "openlf2/engine/relay_link.hpp"
#include "openlf2/engine/room_host.hpp"
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
using namespace openlf2;
namespace {
struct Peer {
    std::unique_ptr<NetworkTransport> socket;
    std::string received;
    bool hello = false;
    bool next(std::string& line) {
        const auto end = received.find('\n');
        if (end == std::string::npos) return false;
        line = received.substr(0, end);
        received.erase(0, end + 1);
        return true;
    }
    bool send(const std::string& line) {
        const auto text = line + "\n";
        return static_cast<bool>(socket->send(std::span<const char>(text.data(), text.size())));
    }
};
int fail(const std::string& message) { std::cerr << "FAIL: " << message << '\n'; return 1; }
}
int main(int argc, char** argv) {
    if (argc < 4) return fail("usage: relay-link-runner RELAY_PORT HOST_TICKET JOIN_TICKET");
    const auto relay_port = static_cast<std::uint16_t>(std::atoi(argv[1]));
    const std::string profile(64, 'a');
    auto host = RoomHost::create(2, profile);
    if (!host) return fail(host.error().message);
    if (!(*host)->listen("127.0.0.1", 0)) return fail("room listen");
    RelayHostBridge bridge;
    if (!bridge.offer("127.0.0.1", relay_port, argv[2])) return fail("relay offer");
    if (make_relay_transport(nullptr, argv[3])) return fail("null socket accepted");
    {
        auto socket = make_network_transport();
        if (!socket || make_relay_transport(std::move(*socket), "short")) return fail("invalid ticket accepted");
    }
    Peer leader, joiner;
    {
        auto socket = make_network_transport();
        if (!socket) return fail("socket");
        leader.socket = std::move(*socket);
        if (!leader.socket->connect("127.0.0.1", (*host)->port())) return fail("leader connect");
        auto relay_socket = make_network_transport();
        if (!relay_socket) return fail("socket");
        auto relay = make_relay_transport(std::move(*relay_socket), argv[3]);
        if (!relay) return fail(relay.error().message);
        joiner.socket = std::move(*relay);
        if (!joiner.socket->connect("127.0.0.1", relay_port)) return fail("joiner connect");
        if (joiner.socket->send(std::span<const char>("x", 1))) return fail("unpaired relay accepted data");
    }
    bool ready_sent = false, started = false;
    int leader_frames = 0, joiner_frames = 0, joiner_sent = 0, leader_sent = 0;
    const int delay = 3, frames = 40;
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(20);
    while (std::chrono::steady_clock::now() < deadline) {
        if (!(*host)->poll()) return fail("room poll");
        bridge.poll((*host)->port());
        for (auto* peer : {&leader, &joiner}) {
            auto bytes = peer->socket->poll();
            if (!bytes) return fail(std::string(peer == &leader ? "leader" : "joiner") + ": " + bytes.error().message +
                                    " / bridge: " + bridge.last_error());
            peer->received.append(bytes->begin(), bytes->end());
            if (!peer->hello && peer->socket->status() == NetworkStatus::connected) {
                peer->hello = true;
                peer->send(std::string(R"({"op":"hello","protocol":2,"profile":")") + profile + R"(","name":")" +
                           (peer == &leader ? "host" : "guest") + "\"}");
            }
        }
        std::string line;
        while (leader.next(line)) {
            if (line.find(R"("op":"lobby")") != std::string::npos && line.find(R"("slot":1)") != std::string::npos && !ready_sent) {
                ready_sent = true;
                leader.send(R"({"op":"ready","value":true})");
                joiner.send(R"({"op":"ready","value":true})");
            } else if (line.find(R"("op":"lobby")") != std::string::npos && ready_sent && !started &&
                       line.find(R"("ready":false)") == std::string::npos) {
                started = true;
                leader.send(R"({"op":"start","delay":3})");
            } else if (line.find(R"("op":"start")") != std::string::npos) {
                // The leader runs `delay` frames ahead, as the game client does.
                for (; leader_sent < delay; ++leader_sent)
                    leader.send(R"({"op":"input","frame":)" + std::to_string(leader_sent) + R"(,"keys":"r"})");
            } else if (line.find(R"("op":"frame")") != std::string::npos) {
                ++leader_frames;
                if (leader_sent < frames) {
                    leader.send(R"({"op":"input","frame":)" + std::to_string(leader_sent) + R"(,"keys":"r"})");
                    ++leader_sent;
                }
            }
            else if (line.find(R"("op":"error")") != std::string::npos || line.find(R"("op":"abort")") != std::string::npos)
                return fail("leader got " + line);
        }
        while (joiner.next(line)) {
            if (line.find(R"("op":"start")") != std::string::npos) {
                if (line.find(R"("delay":3)") == std::string::npos) return fail("delay not relayed: " + line);
                for (; joiner_sent < delay; ++joiner_sent)
                    joiner.send(R"({"op":"input","frame":)" + std::to_string(joiner_sent) + R"(,"keys":""})");
            } else if (line.find(R"("op":"frame")") != std::string::npos) {
                if (line.find(R"("frame":)" + std::to_string(joiner_frames) + ",") == std::string::npos)
                    return fail("joiner tick out of order: " + line);
                ++joiner_frames;
                if (joiner_sent < frames) {
                    joiner.send(R"({"op":"input","frame":)" + std::to_string(joiner_sent) + R"(,"keys":"l"})");
                    ++joiner_sent;
                }
            } else if (line.find(R"("op":"error")") != std::string::npos || line.find(R"("op":"abort")") != std::string::npos)
                return fail("joiner got " + line);
        }
        if (leader_frames == frames && joiner_frames == frames) {
            if (bridge.active() != 1 || bridge.waiting() != 0) return fail("bridge channel counts");
            std::cout << "PASS: room through relay, 2 devices, input delay 3, " << frames << " ordered ticks\n";
            return 0;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    return fail("timeout: leader " + std::to_string(leader_frames) + " joiner " + std::to_string(joiner_frames) +
                " bridge " + bridge.last_error());
}
