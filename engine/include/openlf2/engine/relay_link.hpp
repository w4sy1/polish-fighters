// SPDX-License-Identifier: MIT
#pragma once
#include "openlf2/ports/network.hpp"
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace openlf2 {
// Client side of tools/room_relay.py: after the TCP connection the device sends one JSON
// line with its single-use ticket and waits for {"status":"paired"}; from then on the
// channel is a transparent byte stream, so the room protocol itself is unchanged.
// status() stays "connecting" until the relay has paired the channel.
Result<std::unique_ptr<NetworkTransport>> make_relay_transport(std::unique_ptr<NetworkTransport> inner,
                                                               std::string ticket);
[[nodiscard]] bool valid_relay_ticket(std::string_view ticket) noexcept;

// Host side: every relay channel the host offers waits for one joining device. Once paired,
// it is spliced to a fresh loopback connection to the local RoomHost.
class RelayHostBridge {
public:
    Result<void> offer(std::string_view relay_address, std::uint16_t relay_port, std::string ticket);
    // Pumps all channels; channels that fail or close are dropped (their player leaves the room).
    void poll(std::uint16_t room_port);
    [[nodiscard]] int waiting() const noexcept;
    [[nodiscard]] int active() const noexcept;
    [[nodiscard]] const std::string& last_error() const noexcept { return last_error_; }
    void close() noexcept;
private:
    struct Channel {
        std::unique_ptr<NetworkTransport> relay, local;
        std::string to_local;
        bool dead = false;
    };
    std::vector<Channel> channels_;
    std::string last_error_;
};
}
