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
   assert(!room->submit(0,frame+1,"r"));
   for(int i=count-1;i>=0;--i){auto tick=room->submit(i,frame,i%2?"lc":"r");assert(tick);
    if(i==0){assert(*tick && (*tick)->frame==frame);for(int j=0;j<count;++j)assert((*tick)->inputs[j]==(j%2?"lc":"r"));}
    else assert(!*tick);
   }
   assert(!room->submit(0,frame+1,"r"));
   for(int i=0;i<count;++i)assert(room->checksum(i,frame,state));
  }
  room->leave(1);assert(room->phase()==RoomPhase::aborted);assert(!room->submit(0,60,"r"));
 }
 auto room=Room::create(8,profile);assert(room);assert(room->join(profile,"a"));assert(!room->start(0));
 assert(room->join(profile,"b"));assert(room->ready(0,true));assert(room->ready(1,true));assert(room->start(0));
 assert(room->submit(0,0,"r"));assert(!room->submit(0,0,"r"));assert(room->submit(1,0,"l"));
 assert(room->checksum(0,0,state));assert(!room->checksum(1,0,std::string(64,'c')));assert(room->phase()==RoomPhase::aborted);
 std::cout<<"PASS: 2..8 peer room rules, 60 ticks each, capacity, profile checks, readiness, ordered inputs, checksum barrier, disconnect/desync abort\n";
}
