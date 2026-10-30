#include "openlf2/resources/background_data.hpp"
#include <cassert>
#include <iostream>
#include <string>
int main() {
    std::string source="name: Extended\nwidth: 2400\nzboundary: 300 450\n";
    const std::string layer="layer:\n pic: test.bmp\n transparency: 1\n width: 2400\n x: 0\n y: 128\nlayer_end\n";
    for (int index=0; index<154; ++index) source+=layer;
    auto actual=openlf2::background_data::parse(source);
    assert(actual && actual->layers.size()==154);
    for (int index=154; index<256; ++index) source+=layer;
    auto boundary=openlf2::background_data::parse(source);
    assert(boundary && boundary->layers.size()==256);
    auto rejected=openlf2::background_data::parse(source+layer);
    assert(!rejected && rejected.error().code==openlf2::ErrorCode::unsupported);
    std::cout << "PASS: retains 154 and 256 layers, rejects 257\n";
}
