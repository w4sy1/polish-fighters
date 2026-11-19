// SPDX-License-Identifier: MIT
#pragma once
#include "openlf2/core/result.hpp"
#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace openlf2 {
enum class RoomPhase { lobby, playing, aborted };
struct RoomPeer { int slot; std::string name; bool ready=false; };
struct RoomTick { std::uint64_t frame; std::array<std::string,8> inputs; };
// Platform-neutral room rules. Socket fan-out and game binding are separate adapters.
// Protocol 2: clients submit inputs ahead of the simulated frame (input delay), so a
// tick is emitted as soon as every peer's input for it is known. State checksums are
// verified in the background and only abort on a mismatch or when one stays overdue.
class Room {
public:
    static constexpr std::uint64_t input_window=32;      // frames a peer may submit ahead
    static constexpr std::uint64_t checksum_deadline=300; // frames a checksum may stay incomplete
    static constexpr std::size_t pending_checksum_limit=64;
    static Result<Room> create(int capacity, std::string profile);
    Result<int> join(std::string profile, std::string name);
    Result<void> ready(int slot, bool value);
    Result<void> start(int requester);
    // Returns the ticks completed by this input, in frame order (usually zero or one).
    Result<std::vector<RoomTick>> submit(int slot, std::uint64_t frame, std::string buttons);
    Result<void> checksum(int slot, std::uint64_t frame, std::string value);
    void leave(int slot);
    [[nodiscard]] RoomPhase phase() const { return phase_; }
    [[nodiscard]] const std::map<int,RoomPeer>& peers() const { return peers_; }
    [[nodiscard]] int capacity() const { return capacity_; }
    [[nodiscard]] std::uint64_t frame() const { return frame_; }
private:
    Room(int capacity,std::string profile):capacity_(capacity),profile_(std::move(profile)){}
    int capacity_;
    std::string profile_;
    RoomPhase phase_=RoomPhase::lobby;
    std::map<int,RoomPeer> peers_;
    std::map<std::uint64_t,std::map<int,std::string>> inputs_,checksums_;
    std::uint64_t frame_=0;
    std::optional<std::uint64_t> verified_; // newest frame whose checksums all agreed
};
}
