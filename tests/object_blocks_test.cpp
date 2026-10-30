#include "openlf2/resources/object_data.hpp"
#include "openlf2/resources/data_file.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char**argv){
 std::string header="<bmp_begin>\nname: Test\n<bmp_end>\n<frame> 0 stand\n pic: 0 state: 0 wait: 1 next: 0\n";
 std::string body;
 for(int i=0;i<16;++i)body+="itr:\n kind: 0 x: 0 y: 0 w: 2 h: 2\nitr_end:\n";
 auto sixteen=openlf2::object_data::parse(header+body+"<frame_end>\n");assert(sixteen);assert(sixteen->frames[0].interactions.size()==16);
 assert(!openlf2::object_data::parse(header+body+"itr:\n kind: 0\nitr_end:\n<frame_end>\n"));
 if(argc==2){
  std::ifstream input(argv[1],std::ios::binary);std::string raw((std::istreambuf_iterator<char>(input)),{});
  auto decoded=openlf2::decode_data_file(std::span<const char>(raw.data(),raw.size()));assert(decoded);
  auto data=openlf2::object_data::parse(std::string_view(decoded->data(),decoded->size()));
  if(!data){std::cerr<<data.error().message<<'\n';return 1;}
  std::size_t largest=0;for(const auto&frame:data->frames)largest=std::max(largest,frame.interactions.size());
  std::cout<<"PASS: "<<data->name<<" parsed, largest frame has "<<largest<<" itr blocks\n";
 }
 std::cout<<"PASS: accepts 16 interaction blocks, rejects 17; no attack blocks discarded\n";
}
