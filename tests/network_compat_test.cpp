#include "openlf2/ports/network.hpp"
#include <cassert>
#include <chrono>
#include <iostream>
#include <thread>
int main(){
 auto server=openlf2::make_network_transport(),client=openlf2::make_network_transport();assert(server&&client);
 assert((*server)->listen("127.0.0.1",0));assert((*client)->connect("127.0.0.1",(*server)->local_port()));
 const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
 bool sent=false;std::string received;
 while(std::chrono::steady_clock::now()<deadline){
  auto input=(*client)->poll();assert(input);
  auto peer=(*server)->poll();assert(peer);received.append(peer->begin(),peer->end());
  if(!sent && (*client)->status()==openlf2::NetworkStatus::connected){
   std::string text="legacy-two-peer";assert((*client)->send(std::span<const char>(text.data(),text.size())));sent=true;
  }
  if(received=="legacy-two-peer"){std::cout<<"PASS: legacy two-peer TCP listen/connect/poll unchanged\n";return 0;}
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
 return 1;
}
