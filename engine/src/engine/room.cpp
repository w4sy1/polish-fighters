// SPDX-License-Identifier: MIT
#include "openlf2/engine/room.hpp"
#include <algorithm>
namespace openlf2 {
namespace {
bool digest(const std::string& value) {
    return value.size()==64 && value.find_first_not_of("0123456789abcdef")==std::string::npos;
}
}
Result<Room> Room::create(int capacity,std::string profile) {
    if(capacity<2 || capacity>8) return fail(ErrorCode::limit,"room capacity must be 2..8 devices");
    if(!digest(profile)) return fail(ErrorCode::format,"profile must be a SHA-256 fingerprint");
    return Room(capacity,std::move(profile));
}
Result<int> Room::join(std::string profile,std::string name) {
    if(phase_!=RoomPhase::lobby) return fail(ErrorCode::format,"room already started or aborted");
    if(profile!=profile_) return fail(ErrorCode::dependency,"engine, scripts or pack profile mismatch");
    if(peers_.size()>=static_cast<std::size_t>(capacity_)) return fail(ErrorCode::limit,"room full");
    if(name.empty() || name.size()>24 || std::ranges::any_of(name,[](unsigned char c){return c<32 || c==127;}))
        return fail(ErrorCode::format,"invalid player name");
    int slot=0;while(peers_.contains(slot))++slot;
    peers_.emplace(slot,RoomPeer{slot,std::move(name),false});return slot;
}
Result<void> Room::ready(int slot,bool value) {
    if(phase_!=RoomPhase::lobby || !peers_.contains(slot))return fail(ErrorCode::format,"invalid lobby peer");
    peers_.at(slot).ready=value;return {};
}
Result<void> Room::start(int requester) {
    if(phase_!=RoomPhase::lobby || peers_.size()<2)return fail(ErrorCode::format,"at least two devices are required");
    if(requester!=peers_.begin()->first)return fail(ErrorCode::format,"only the room leader can start");
    for(const auto& [slot,peer]:peers_)if(!peer.ready)return fail(ErrorCode::format,"every player must be ready");
    phase_=RoomPhase::playing;return {};
}
Result<std::optional<RoomTick>> Room::submit(int slot,std::uint64_t frame,std::string buttons) {
    if(phase_!=RoomPhase::playing || !peers_.contains(slot))return fail(ErrorCode::format,"invalid match peer");
    if(checksum_frame_)return fail(ErrorCode::format,"waiting for state checksums");
    if(frame!=frame_)return fail(ErrorCode::format,"out-of-order input frame");
    if(buttons.size()>7 || buttons.find_first_not_of("udlrcbf")!=std::string::npos)
        return fail(ErrorCode::format,"invalid input buttons");
    for(char key:buttons)if(std::count(buttons.begin(),buttons.end(),key)>1)return fail(ErrorCode::format,"duplicate input button");
    if(!inputs_.emplace(slot,std::move(buttons)).second)return fail(ErrorCode::format,"duplicate input frame");
    if(inputs_.size()!=peers_.size())return std::optional<RoomTick>{};
    RoomTick tick{frame_,{}};
    for(const auto& [id,value]:inputs_)tick.inputs[id]=value;
    inputs_.clear();checksum_frame_=frame_++;return std::optional<RoomTick>{std::move(tick)};
}
Result<void> Room::checksum(int slot,std::uint64_t frame,std::string value) {
    if(phase_!=RoomPhase::playing || !peers_.contains(slot) || !checksum_frame_ || *checksum_frame_!=frame || !digest(value))
        return fail(ErrorCode::format,"invalid checksum report");
    if(!checksums_.empty() && checksums_.begin()->second!=value){phase_=RoomPhase::aborted;return fail(ErrorCode::format,"simulation desynchronized");}
    if(!checksums_.emplace(slot,std::move(value)).second)return fail(ErrorCode::format,"duplicate checksum report");
    if(checksums_.size()==peers_.size()){checksums_.clear();checksum_frame_.reset();}
    return {};
}
void Room::leave(int slot) {
    if(!peers_.erase(slot))return;
    if(phase_==RoomPhase::playing){phase_=RoomPhase::aborted;inputs_.clear();checksums_.clear();}
}
}
