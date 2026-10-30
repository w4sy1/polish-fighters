// SPDX-License-Identifier: MIT
#pragma once
#include "openlf2/core/result.hpp"
#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <string>

namespace openlf2 {
enum class RoomPhase { lobby, playing, aborted };
struct RoomPeer { int slot; std::string name; bool ready=false; };
struct RoomTick { std::uint64_t frame; std::array<std::string,8> inputs; };
// Platform-neutral room rules. Socket fan-out and game binding are separate adapters.
class Room {
public:
    static Result<Room> create(int capacity, std::string profile);
    Result<int> join(std::string profile, std::string name);
    Result<void> ready(int slot, bool value);
    Result<void> start(int requester);
    Result<std::optional<RoomTick>> submit(int slot, std::uint64_t frame, std::string buttons);
    Result<void> checksum(int slot, std::uint64_t frame, std::string value);
    void leave(int slot);
    [[nodiscard]] RoomPhase phase() const { return phase_; }
    [[nodiscard]] const std::map<int,RoomPeer>& peers() const { return peers_; }
    [[nodiscard]] int capacity() const { return capacity_; }
    [[nodiscard]] std::uint64_t frame() const { return frame_; }
    [[nodiscard]] bool waiting_for_checksums() const { return checksum_frame_.has_value(); }
private:
    Room(int capacity,std::string profile):capacity_(capacity),profile_(std::move(profile)){}
    int capacity_;
    std::string profile_;
    RoomPhase phase_=RoomPhase::lobby;
    std::map<int,RoomPeer> peers_;
    std::map<int,std::string> inputs_,checksums_;
    std::uint64_t frame_=0;
    std::optional<std::uint64_t> checksum_frame_;
};
}
