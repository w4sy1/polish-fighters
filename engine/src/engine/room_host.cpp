// SPDX-License-Identifier: MIT
#include "openlf2/engine/room_host.hpp"
#include "openlf2/core/json.hpp"
#include "openlf2/ports/network.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <utility>
namespace openlf2 {
namespace {
using Clock=std::chrono::steady_clock;
ScriptValue object(ScriptTable table){return ScriptValue{std::move(table)};}
const ScriptValue* field(const ScriptValue& value,std::string_view key){
 const auto* fields=std::get_if<ScriptTable>(&value.value);if(!fields)return nullptr;
 for(const auto& item:*fields){const auto* name=std::get_if<std::string>(&item.key);if(name && *name==key)return &item.value;}
 return nullptr;
}
const std::string* text(const ScriptValue& value,std::string_view key){const auto* v=field(value,key);return v?std::get_if<std::string>(&v->value):nullptr;}
const std::int32_t* number(const ScriptValue& value,std::string_view key){const auto* v=field(value,key);return v?std::get_if<std::int32_t>(&v->value):nullptr;}
const bool* boolean(const ScriptValue& value,std::string_view key){const auto* v=field(value,key);return v?std::get_if<bool>(&v->value):nullptr;}
}
struct RoomHost::Impl {
 struct Peer {
  std::unique_ptr<NetworkTransport> socket;
  std::optional<int> slot;
  std::string input;
  std::optional<ScriptValue> queued_input;
  Clock::time_point last=Clock::now(),close_at{};
  bool closing=false,dead=false;
 };
 Room room;
 std::unique_ptr<NetworkTransport> listener;
 std::vector<Peer> peers;
 std::int32_t seed;
 std::string functions;
 std::int32_t unlock=0;
 std::chrono::milliseconds timeout;
 Impl(Room value,std::int32_t random_seed,std::chrono::milliseconds idle):room(std::move(value)),seed(random_seed),timeout(idle){}
 bool send(Peer& peer,const ScriptValue& message){
  auto serialized=write_json(message);
  if(!serialized){peer.dead=true;return false;}
  // The settings writer is pretty-printed. Wire messages must occupy one line;
  // remove whitespace only outside JSON strings, preserving escapes and names.
  std::string compact;bool quoted=false,escaped=false;
  for(char byte:*serialized){
   if(quoted){compact+=byte;if(escaped)escaped=false;else if(byte=='\\')escaped=true;else if(byte=='"')quoted=false;}
   else if(byte=='"'){quoted=true;compact+=byte;}
   else if(byte!=' ' && byte!='\n' && byte!='\r' && byte!='\t')compact+=byte;
  }
  *serialized=std::move(compact);
  if(serialized->size()>4096){peer.dead=true;return false;}
  *serialized+='\n';
  auto result=peer.socket->send(std::span<const char>(serialized->data(),serialized->size()));
  if(!result){peer.dead=true;return false;}return true;
 }
 void broadcast(const ScriptValue& message){for(auto& peer:peers)if(peer.slot && !peer.closing && !peer.dead)send(peer,message);}
 void soft_error(Peer& peer,std::string reason){
  send(peer,object({{"op",ScriptValue{std::string("error")}},{"reason",ScriptValue{std::move(reason)}}}));
 }
 void reject(Peer& peer,std::string reason){
  soft_error(peer,std::move(reason));
  peer.closing=true;peer.close_at=Clock::now()+std::chrono::milliseconds(50);
 }
 void lobby(){
  ScriptTable list;int index=1;
  for(const auto& [slot,peer]:room.peers())list.push_back({index++,object({{"slot",ScriptValue{static_cast<std::int32_t>(slot)}},{"name",ScriptValue{peer.name}},{"ready",ScriptValue{peer.ready}}})});
  broadcast(object({{"op",ScriptValue{std::string("lobby")}},{"capacity",ScriptValue{static_cast<std::int32_t>(room.capacity())}},{"peers",object(std::move(list))}}));
 }
 void abort(){broadcast(object({{"op",ScriptValue{std::string("abort")}},{"reason",ScriptValue{std::string("peer disconnected, timed out or simulation desynchronized")}}}));}
 void handle(Peer& peer,const ScriptValue& value){
  const auto* op=text(value,"op");if(!op){reject(peer,"missing operation");return;}
  if(!peer.slot){
   const auto* version=number(value,"protocol");const auto* profile=text(value,"profile");const auto* name=text(value,"name");
   if(*op!="hello" || !version || *version!=1 || !profile || !name){reject(peer,"invalid protocol greeting");return;}
   auto joined=room.join(*profile,*name);if(!joined){reject(peer,joined.error().message);return;}
   peer.slot=*joined;
   send(peer,object({{"op",ScriptValue{std::string("welcome")}},{"slot",ScriptValue{static_cast<std::int32_t>(*joined)}},{"capacity",ScriptValue{static_cast<std::int32_t>(room.capacity())}}}));lobby();return;
  }
  if(*op=="ping"){
   send(peer,object({{"op",ScriptValue{std::string("pong")}}}));
  }else if(*op=="ready"){
   const auto* ready=boolean(value,"value");if(!ready){reject(peer,"missing ready value");return;}
   auto changed=room.ready(*peer.slot,*ready);if(!changed){soft_error(peer,changed.error().message);return;}lobby();
  }else if(*op=="start"){
   auto started=room.start(*peer.slot);if(!started){soft_error(peer,started.error().message);return;}
   broadcast(object({{"op",ScriptValue{std::string("start")}},{"seed",ScriptValue{seed}},{"frame",ScriptValue{std::int32_t{0}}}}));
  }else if(*op=="input"){
   const auto* frame=number(value,"frame");const auto* keys=text(value,"keys");
   if(!frame || *frame<0 || !keys){reject(peer,"invalid input frame");return;}
   const auto* commands=text(value,"functions");const auto* marks=number(value,"unlock");
   if((commands && (commands->size()>9 || commands->find_first_not_of("123456789")!=std::string::npos)) ||
      (marks && (*marks<0 || *marks>3)) || (*peer.slot!=0 && ((commands && !commands->empty()) || (marks && *marks!=0)))) {
    reject(peer,"only the host may submit global commands");return;
   }
   // Accept at most the next input while the preceding checksums are in flight.
   // Simulation still cannot advance until every checksum agrees.
   if(room.waiting_for_checksums()){
    if(static_cast<std::uint64_t>(*frame)!=room.frame()){reject(peer,"out-of-order queued input frame");return;}
    if(peer.queued_input){reject(peer,"duplicate queued input frame");return;}
    peer.queued_input=value;return;
   }
   if(*peer.slot==0){functions=commands?*commands:"";unlock=marks?*marks:0;}
   auto tick=room.submit(*peer.slot,static_cast<std::uint64_t>(*frame),*keys);
   if(!tick){reject(peer,tick.error().message);return;}
   if(*tick){
    ScriptTable inputs;for(int slot=0;slot<8;++slot)inputs.push_back({slot+1,ScriptValue{(**tick).inputs[static_cast<std::size_t>(slot)]}});
    broadcast(object({{"op",ScriptValue{std::string("frame")}},{"frame",ScriptValue{*frame}},{"inputs",object(std::move(inputs))},{"functions",ScriptValue{functions}},{"unlock",ScriptValue{unlock}}}));
   }
  }else if(*op=="checksum"){
   const auto* frame=number(value,"frame");const auto* state=text(value,"state");
   if(!frame || *frame<0 || !state){reject(peer,"invalid checksum frame");return;}
   auto checked=room.checksum(*peer.slot,static_cast<std::uint64_t>(*frame),*state);
   if(!checked){reject(peer,checked.error().message);if(room.phase()==RoomPhase::aborted)abort();return;}
   if(!room.waiting_for_checksums()){
    broadcast(object({{"op",ScriptValue{std::string("checked")}},{"frame",ScriptValue{*frame}}}));
    for(auto& waiting:peers){
     if(waiting.queued_input && !waiting.closing && !waiting.dead){
      auto input=std::move(*waiting.queued_input);waiting.queued_input.reset();handle(waiting,input);
     }
    }
   }
  }else reject(peer,"unknown operation");
 }
};
RoomHost::RoomHost(std::unique_ptr<Impl> impl):impl_(std::move(impl)){}
RoomHost::~RoomHost()=default;
Result<std::unique_ptr<RoomHost>> RoomHost::create(int capacity,std::string profile,std::int32_t seed,std::chrono::milliseconds timeout){
 auto room=Room::create(capacity,std::move(profile));if(!room)return std::unexpected(room.error());
 if(timeout<std::chrono::milliseconds(50))return fail(ErrorCode::format,"room timeout is too short");
 auto impl=std::make_unique<Impl>(std::move(*room),seed,timeout);
 auto listener=make_network_transport();if(!listener)return std::unexpected(listener.error());impl->listener=std::move(*listener);
 return std::unique_ptr<RoomHost>(new RoomHost(std::move(impl)));
}
Result<void> RoomHost::listen(std::string_view address,std::uint16_t port){return impl_->listener->listen(address,port);}
std::uint16_t RoomHost::port()const{return impl_->listener->local_port();}
const Room& RoomHost::room()const{return impl_->room;}
Result<void> RoomHost::poll(){
 auto& state=*impl_;
 // Bounded accepts/work, pending connections are capped separately from authenticated players.
 for(int count=0;count<16;++count){
  auto accepted=state.listener->accept_peer();if(!accepted)return std::unexpected(accepted.error());
  if(!*accepted)break;
  if(state.peers.size()>=16){(*accepted)->close();continue;}
  Impl::Peer peer;peer.socket=std::move(*accepted);state.peers.push_back(std::move(peer));
 }
 const auto now=Clock::now();
 for(auto& peer:state.peers){
  if(peer.dead)continue;
  if((peer.closing && now>=peer.close_at) || now-peer.last>state.timeout){peer.dead=true;continue;}
  auto bytes=peer.socket->poll();if(!bytes){peer.dead=true;continue;}
  if(!bytes->empty())peer.last=now;
  if(peer.closing)continue;
  peer.input.append(bytes->begin(),bytes->end());
  if(peer.input.size()>8192){state.reject(peer,"receive buffer exceeded");continue;}
  for(int messages=0;messages<32 && !peer.closing && !peer.dead;++messages){
   const auto end=peer.input.find('\n');
   if(end==std::string::npos){if(peer.input.size()>4096)state.reject(peer,"message exceeds 4096 bytes");break;}
   if(end>4096){state.reject(peer,"message exceeds 4096 bytes");break;}
   auto message=parse_json(std::string_view(peer.input).substr(0,end));peer.input.erase(0,end+1);
   if(!message){state.reject(peer,"invalid JSON message");break;}
   state.handle(peer,*message);
  }
 }
 bool changed=false,aborted=false;
 for(auto& peer:state.peers)if(peer.dead){
  if(peer.slot){const bool playing=state.room.phase()==RoomPhase::playing;state.room.leave(*peer.slot);changed=true;aborted=aborted||playing;}
  peer.socket->close();
 }
 std::erase_if(state.peers,[](const auto& peer){return peer.dead;});
 if(aborted)state.abort();else if(changed && state.room.phase()==RoomPhase::lobby)state.lobby();
 return {};
}
}
