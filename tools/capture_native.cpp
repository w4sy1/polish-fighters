#include <dlfcn.h>
#include <cstdlib>
#include <cstdio>
extern "C" bool SDL_RenderPresent(void* renderer) {
    static auto real = reinterpret_cast<bool(*)(void*)>(dlsym(RTLD_NEXT,"SDL_RenderPresent"));
    static int frames=0;
    const char* requested=std::getenv("PF_CAPTURE_FRAME");
    const int capture_frame=requested ? std::atoi(requested) : 12;
    if (++frames == capture_frame) {
        auto read = reinterpret_cast<void*(*)(void*,const void*)>(dlsym(RTLD_NEXT,"SDL_RenderReadPixels"));
        auto save = reinterpret_cast<bool(*)(void*,const char*)>(dlsym(RTLD_NEXT,"SDL_SaveBMP"));
        auto destroy = reinterpret_cast<void(*)(void*)>(dlsym(RTLD_NEXT,"SDL_DestroySurface"));
        auto surface = read(renderer,nullptr);
        const char* path=std::getenv("PF_CAPTURE");
        if (surface && path && save(surface,path)) { destroy(surface); std::fprintf(stderr,"Captured native frame\n");std::exit(0); }
        std::fprintf(stderr,"Failed native capture\n");std::exit(2);
    }
    return real(renderer);
}
