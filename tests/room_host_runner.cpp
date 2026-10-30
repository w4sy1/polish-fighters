#include "openlf2/engine/room_host.hpp"
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <thread>
int main(int argc,char**argv){
 const int capacity=argc>1?std::atoi(argv[1]):8;
 const int timeout=argc>2?std::atoi(argv[2]):5000;
 auto host=openlf2::RoomHost::create(capacity,std::string(64,'a'),42,std::chrono::milliseconds(timeout));
 if(!host){std::cerr<<host.error().message<<'\n';return 1;}
 auto opened=(*host)->listen("127.0.0.1",0);if(!opened){std::cerr<<opened.error().message<<'\n';return 1;}
 std::cout<<"LISTEN 127.0.0.1:"<<(*host)->port()<<std::endl;
 const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);
 while(std::chrono::steady_clock::now()<deadline){
  auto polled=(*host)->poll();if(!polled){std::cerr<<polled.error().message<<'\n';return 1;}
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
}
