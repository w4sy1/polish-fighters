#include "openlf2/resources/object_data.hpp"
#include "openlf2/resources/data_file.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>

namespace {
class ObjectResource final : public openlf2::ResourceSource {
public:
 openlf2::Result<openlf2::Bytes> read(std::string_view) const override {
  const std::string text="<frame> 0 stand\nitr: kind: 0 y: 180000000000 w: 99999999999999999999 itr_end:\n<frame_end>\n";
  return openlf2::Bytes(text.begin(),text.end());
 }
};
}

int main(int argc,char**argv){
 ObjectResource resource;
 auto community=openlf2::object_data::load(resource,"mods/ntsd-community/a/object.txt",999);
 assert(community && community->frames[0].interactions[0].area.y==-388626432);
 assert(community->frames[0].interactions[0].area.width==1661992959);
 auto lf3=openlf2::object_data::load(resource,"mods/lf3/a/object.txt",999);
 assert(lf3 && lf3->frames[0].interactions[0].area.y==-388626432);
 assert(!openlf2::object_data::load(resource,"mods/other/a/object.txt",999));
 auto extended="<bmp_begin>\nname: Extended\n<bmp_end>\n<frame> 998 final\n pic: 0 state: 0 wait: 1 next: 999\n<frame_end>\n";
 assert(!openlf2::object_data::parse(extended));
 auto dbz=openlf2::object_data::parse(extended,openlf2::object_data::extended_frame_count);
 assert(dbz && dbz->frames.size()==999);
 assert(!openlf2::object_data::parse("<bmp_begin>\n<bmp_end>\n<frame> 999 reserved\n<frame_end>\n",999));
 assert(!openlf2::object_data::parse(extended,1000));
 std::string header="<bmp_begin>\nname: Test\n<bmp_end>\n<frame> 0 stand\n pic: 0 state: 0 wait: 1 next: 0\n";
 std::string body;
 for(int i=0;i<16;++i)body+="itr:\n kind: 0 x: 0 y: 0 w: 2 h: 2\nitr_end:\n";
 auto sixteen=openlf2::object_data::parse(header+body+"<frame_end>\n");assert(sixteen);assert(sixteen->frames[0].interactions.size()==16);
 assert(!openlf2::object_data::parse(header+body+"itr:\n kind: 0\nitr_end:\n<frame_end>\n"));
 std::string extended_blocks;
 for(int i=0;i<32;++i)extended_blocks+="itr:\n kind: 0 x: 0 y: 0 w: 2 h: 2\nitr_end:\n";
 auto dbz_blocks=openlf2::object_data::parse(header+extended_blocks+"<frame_end>\n",999);
 assert(dbz_blocks && dbz_blocks->frames[0].interactions.size()==32);
 assert(!openlf2::object_data::parse(header+extended_blocks+"itr:\n kind: 0\nitr_end:\n<frame_end>\n",999));
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
