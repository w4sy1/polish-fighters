// SPDX-License-Identifier: MIT
#include "openlf2/engine/relay_link.hpp"
#include <algorithm>
#include <utility>

namespace openlf2 {
namespace {
constexpr std::string_view paired_line = R"({"status":"paired"})";
constexpr std::size_t header_limit = 1024;
constexpr std::size_t channel_limit = 8;
constexpr std::size_t pending_limit = 65536;

class RelayTransport final : public NetworkTransport {
public:
    RelayTransport(std::unique_ptr<NetworkTransport> inner, std::string ticket)
        : inner_(std::move(inner)), ticket_(std::move(ticket)) {}
    Result<void> listen(std::string_view, std::uint16_t) override {
        return fail(ErrorCode::unsupported, "relay channels only connect");
    }
    Result<void> connect(std::string_view address, std::uint16_t port) override {
        sent_ = paired_ = false;
        header_.clear();
        return inner_->connect(address, port);
    }
    Result<void> send(std::span<const char> bytes) override {
        if (!paired_) return fail(ErrorCode::io, "Relay channel is not paired yet");
        return inner_->send(bytes);
    }
    Result<Bytes> poll() override {
        auto bytes = inner_->poll();
        if (!bytes) return std::unexpected(bytes.error());
        if (paired_) return bytes;
        if (!sent_ && inner_->status() == NetworkStatus::connected) {
            const std::string line = R"({"ticket":")" + ticket_ + "\"}\n";
            auto sent = inner_->send(std::span<const char>(line.data(), line.size()));
            if (!sent) return std::unexpected(sent.error());
            sent_ = true;
        }
        header_.append(bytes->begin(), bytes->end());
        const auto end = header_.find('\n');
        if (end == std::string::npos) {
            if (header_.size() > header_limit) { close(); return fail(ErrorCode::format, "Relay handshake too large"); }
            return Bytes{};
        }
        auto line = std::string_view(header_).substr(0, end);
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.remove_suffix(1);
        if (line != paired_line) {
            std::string reason = "Relay refused the channel: " + std::string(line.substr(0, 160));
            close();
            return fail(ErrorCode::io, std::move(reason));
        }
        paired_ = true;
        Bytes rest(header_.begin() + static_cast<std::ptrdiff_t>(end + 1), header_.end());
        header_.clear();
        return rest;
    }
    void close() noexcept override {
        inner_->close();
        sent_ = paired_ = false;
        header_.clear();
    }
    [[nodiscard]] NetworkStatus status() const noexcept override {
        const auto status = inner_->status();
        return status == NetworkStatus::connected && !paired_ ? NetworkStatus::connecting : status;
    }
    [[nodiscard]] std::uint16_t local_port() const noexcept override { return inner_->local_port(); }

private:
    std::unique_ptr<NetworkTransport> inner_;
    std::string ticket_, header_;
    bool sent_ = false, paired_ = false;
};
}

bool valid_relay_ticket(std::string_view ticket) noexcept {
    return ticket.size() >= 16 && ticket.size() <= 128 && std::ranges::all_of(ticket, [](char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_';
    });
}

Result<std::unique_ptr<NetworkTransport>> make_relay_transport(std::unique_ptr<NetworkTransport> inner,
                                                               std::string ticket) {
    if (!inner) return fail(ErrorCode::format, "missing relay socket");
    if (!valid_relay_ticket(ticket)) return fail(ErrorCode::format, "invalid relay ticket");
    return std::unique_ptr<NetworkTransport>(new RelayTransport(std::move(inner), std::move(ticket)));
}

Result<void> RelayHostBridge::offer(std::string_view relay_address, std::uint16_t relay_port, std::string ticket) {
    if (channels_.size() >= channel_limit) return fail(ErrorCode::limit, "too many relay channels");
    auto socket = make_network_transport();
    if (!socket) return std::unexpected(socket.error());
    auto relay = make_relay_transport(std::move(*socket), std::move(ticket));
    if (!relay) return std::unexpected(relay.error());
    auto connected = (*relay)->connect(relay_address, relay_port);
    if (!connected) return std::unexpected(connected.error());
    Channel channel;
    channel.relay = std::move(*relay);
    channels_.push_back(std::move(channel));
    return {};
}

void RelayHostBridge::poll(std::uint16_t room_port) {
    for (auto& channel : channels_) {
        auto failed = [&](const Error& error) { last_error_ = error.message; channel.dead = true; };
        auto incoming = channel.relay->poll();
        if (!incoming) { failed(incoming.error()); continue; }
        if (channel.relay->status() != NetworkStatus::connected) continue;
        if (!channel.local) {
            auto local = make_network_transport();
            if (!local) { failed(local.error()); continue; }
            auto opened = (*local)->connect("127.0.0.1", room_port);
            if (!opened) { failed(opened.error()); continue; }
            channel.local = std::move(*local);
        }
        channel.to_local.append(incoming->begin(), incoming->end());
        if (channel.to_local.size() > pending_limit) { last_error_ = "relay buffer exceeded"; channel.dead = true; continue; }
        auto outgoing = channel.local->poll();
        if (!outgoing) { failed(outgoing.error()); continue; }
        if (channel.local->status() == NetworkStatus::connected && !channel.to_local.empty()) {
            auto sent = channel.local->send(std::span<const char>(channel.to_local.data(), channel.to_local.size()));
            if (!sent) { failed(sent.error()); continue; }
            channel.to_local.clear();
        }
        if (!outgoing->empty()) {
            auto sent = channel.relay->send(std::span<const char>(outgoing->data(), outgoing->size()));
            if (!sent) { failed(sent.error()); continue; }
        }
    }
    for (auto& channel : channels_) {
        if (!channel.dead) continue;
        channel.relay->close();
        if (channel.local) channel.local->close();
    }
    std::erase_if(channels_, [](const Channel& channel) { return channel.dead; });
}

int RelayHostBridge::waiting() const noexcept {
    return static_cast<int>(std::ranges::count_if(channels_, [](const Channel& channel) {
        return channel.relay->status() != NetworkStatus::connected;
    }));
}

int RelayHostBridge::active() const noexcept {
    return static_cast<int>(channels_.size()) - waiting();
}

void RelayHostBridge::close() noexcept {
    for (auto& channel : channels_) {
        channel.relay->close();
        if (channel.local) channel.local->close();
    }
    channels_.clear();
}
}
