#include "openlf2/engine/room.hpp"
#include <cassert>
#include <iostream>
using namespace openlf2;
const std::string profile(64,'a'),state(64,'b');
int main(){
 assert(!Room::create(1,profile));assert(!Room::create(9,profile));assert(!Room::create(8,"bad"));
 for(int count=2;count<=8;++count){
  auto room=Room::create(count,profile);assert(room);assert(!room->join(std::string(64,'c'),"wrong"));
  for(int i=0;i<count;++i){auto slot=room->join(profile,"player"+std::to_string(i));assert(slot && *slot==i);}
  assert(!room->join(profile,"extra"));assert(!room->start(0));
  for(int i=0;i<count;++i){assert(room->ready(i,true));}
  assert(!room->start(1));assert(room->start(0));
  for(unsigned frame=0;frame<60;++frame){
   assert(!room->submit(0,frame+Room::input_window,"r"));
   for(int i=count-1;i>=0;--i){auto ticks=room->submit(i,frame,i%2?"lc":"r");assert(ticks);
    if(i==0){assert(ticks->size()==1 && (*ticks)[0].frame==frame);for(int j=0;j<count;++j)assert((*ticks)[0].inputs[j]==(j%2?"lc":"r"));}
    else assert(ticks->empty());
   }
   assert(!room->submit(0,frame,"r"));
   if(frame%30==0)for(int i=0;i<count;++i)assert(room->checksum(i,frame,state));
  }
  room->leave(1);assert(room->phase()==RoomPhase::aborted);assert(!room->submit(0,60,"r"));
 }
 auto started=[]{
  auto room=Room::create(2,profile);assert(room);assert(room->join(profile,"a"));assert(room->join(profile,"b"));
  assert(room->ready(0,true));assert(room->ready(1,true));assert(room->start(0));return std::move(*room);
 };
 {
  // Input delay: both peers run ahead, ticks are released in order once complete.
  auto room=started();
  for(unsigned frame=0;frame<6;++frame){auto ticks=room.submit(0,frame,"r");assert(ticks && ticks->empty());}
  assert(room.submit(1,2,"l")->empty());assert(room.submit(1,1,"l")->empty());
  auto ticks=room.submit(1,0,"l");assert(ticks && ticks->size()==3);
  for(unsigned i=0;i<3;++i)assert((*ticks)[i].frame==i && (*ticks)[i].inputs[0]=="r" && (*ticks)[i].inputs[1]=="l");
  assert(room.frame()==3);assert(!room.submit(1,1,"l"));
  // Checksums never block input; a future frame cannot be reported.
  assert(!room.checksum(0,3,state));assert(room.checksum(0,0,state));assert(room.submit(1,3,"")->size()==1);
  assert(room.checksum(1,0,state));assert(!room.checksum(1,0,state));
 }
 {
  auto room=started();
  assert(room.submit(0,0,"r"));assert(!room.submit(0,0,"r"));assert(room.submit(1,0,"l"));
  assert(room.checksum(0,0,state));assert(!room.checksum(1,0,std::string(64,'c')));assert(room.phase()==RoomPhase::aborted);
 }
 {
  // A peer that never reports its checksum cannot keep the match running forever.
  auto room=started();assert(!room.checksum(0,0,state));
  assert(room.submit(0,0,"")->empty());assert(room.submit(1,0,"")->size()==1);assert(room.checksum(0,0,state));
  bool aborted=false;
  for(std::uint64_t frame=1;frame<Room::checksum_deadline+5 && !aborted;++frame){
   auto first=room.submit(0,frame,"");if(!first){aborted=true;break;}
   auto second=room.submit(1,frame,"");if(!second)aborted=true;
  }
  assert(aborted && room.phase()==RoomPhase::aborted);
 }
 std::cout<<"PASS: 2..8 peer room rules, 60 ticks each, input delay window, ordered ticks, background checksums, overdue/disconnect/desync abort\n";
}
