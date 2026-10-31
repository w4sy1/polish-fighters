// Own diagnostic program, calling only the installed Microsoft system CRT.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <iostream>
#include <string>
#pragma comment(linker, "/manifestdependency:\"type='win32' name='Microsoft.VC80.CRT' version='8.0.50727.9680' processorArchitecture='x86' publicKeyToken='1fc8b3b9a1e18e3b'\"")
int main() {
    const auto module=LoadLibraryW(L"MSVCR80.dll");
    if (!module) return 2;
    using Scan=int(__cdecl*)(const char*,const char*,...);
    const auto scan=reinterpret_cast<Scan>(GetProcAddress(module,"sscanf"));
    if (!scan) return 3;
    std::string token;
    while (std::cin>>token) {
        int value=0;
        const int converted=scan(token.c_str(),"%d",&value);
        std::cout<<token<<" "<<converted<<" "<<value<<"\n";
    }
    FreeLibrary(module);
}
