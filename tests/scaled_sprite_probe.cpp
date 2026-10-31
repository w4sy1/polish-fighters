// Render real atlas source rectangles through the production SDL platform.
#include "openlf2/ports/platform.hpp"
#include <SDL3/SDL.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>

using namespace openlf2;
class Assets final : public ResourceSource {
public:
    explicit Assets(std::filesystem::path root) : root_(std::move(root)) {}
    Result<Bytes> read(std::string_view name) const override {
        std::string resource(name);
        const std::string prefix="mods/polish-originals/";
        std::filesystem::path path;
        if (resource.starts_with(prefix)) path=root_/"content-packs/polish-originals/art"/resource.substr(prefix.size());
        else if (resource.starts_with("base/")) path=root_/"engine/scripts"/resource;
        else return fail(ErrorCode::io,"probe unknown resource: "+resource);
        std::ifstream input(path,std::ios::binary);
        if (!input) return fail(ErrorCode::io,"probe missing resource: "+resource);
        return Bytes(std::istreambuf_iterator<char>(input),{});
    }
private:
    std::filesystem::path root_;
};
class Silent final : public MusicDecoder {
    Result<std::unique_ptr<MusicStream>> open(Bytes) const override {
        return fail(ErrorCode::unsupported,"music unused by render probe");
    }
};
int main(int argc,char** argv) {
    if (argc!=4) return 2;
    SDL_SetHint(SDL_HINT_VIDEO_DRIVER,"dummy");
    SDL_SetHint(SDL_HINT_AUDIO_DRIVER,"dummy");
    Assets assets(argv[1]);Silent decoder;
    const Viewport viewport{1200,720,24,32,48};
    auto platform=make_platform(assets,viewport,decoder,"software");
    if (!platform) { std::cerr<<platform.error().message;return 3; }
    std::ifstream input(argv[2]);
    std::vector<DrawCommand> commands;
    std::string resource;int sx,sy,sw,sh,x,y,w,h,flip;
    while (input>>resource>>sx>>sy>>sw>>sh>>x>>y>>w>>h>>flip) {
        SpriteCommand sprite{resource,{sx,sy,sw,sh},x,y,false};
        sprite.destination_width=w;sprite.destination_height=h;sprite.mirrored=flip!=0;
        commands.emplace_back(std::move(sprite));
    }
    if (commands.size()!=64) return 4;
    auto result=(*platform)->present(commands,viewport);
    if (!result) { std::cerr<<result.error().message;return 5; }
    int count=0;SDL_Window** windows=SDL_GetWindows(&count);
    if (!windows || count!=1) return 6;
    SDL_Renderer* renderer=SDL_GetRenderer(windows[0]);SDL_free(windows);
    SDL_Surface* snapshot=SDL_RenderReadPixels(renderer,nullptr);
    if (!snapshot) { std::cerr<<SDL_GetError();return 7; }
    const bool saved=SDL_SaveBMP(snapshot,argv[3]);
    SDL_DestroySurface(snapshot);
    if (!saved) return 8;
    std::cout<<"PASS: 64 atlas poses, scaled and mirrored, production SDL software renderer\n";
    return 0;
}
