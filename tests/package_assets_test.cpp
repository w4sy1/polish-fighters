#include "openlf2/engine/packages.hpp"
#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    static_assert(openlf2::package_asset_limit("mods/test/music.wma") == 64 * 1024 * 1024);
    static_assert(openlf2::package_asset_limit("mods/test/sprite.bmp") == 16 * 1024 * 1024);
    static_assert(openlf2::package_asset_limit("mods/test/data.dat") == 16 * 1024 * 1024);
    namespace fs = std::filesystem;
    const auto temporary = fs::temp_directory_path();
    const auto root = temporary / ("pf-asset-limit-" + std::to_string(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    if (!fs::create_directory(root)) return 2;
    struct Cleanup {
        fs::path path;
        ~Cleanup() { std::error_code error; fs::remove_all(path, error); }
    } cleanup{root};
    const auto base = root / "base", extra = root / "extra";
    fs::create_directory(base); fs::create_directory(extra);
    std::ofstream(base / "asset.bin") << "fixture";
    std::ofstream(extra / "asset.bin") << "fixture";
    const auto write = [](const fs::path& folder, const std::string& id, int count) {
        std::ofstream manifest(folder / "package.manifest");
        manifest << "id=" << id << "\nversion=1\napi=1\n";
        manifest << (id == "base" ? "window=794x550\n" : "requires=base@1\n");
        for (int i = 0; i < count; ++i)
            manifest << "asset=mods/" << id << "/" << i << "|asset.bin\n";
    };
    const std::vector<fs::path> roots{base, extra};
    write(base, "base", 2048); write(extra, "extra", 2048);
    auto loaded = openlf2::load_packages(roots);
    assert(loaded && loaded->assets.size() == 4096);
    write(extra, "extra", 2049);
    loaded = openlf2::load_packages(roots);
    assert(!loaded && loaded.error().code == openlf2::ErrorCode::limit);
    write(base, "base", 0); write(extra, "mixed-all", 12288);
    loaded = openlf2::load_packages(roots);
    assert(loaded && loaded->assets.size() == 12288);
    write(extra, "mixed-all", 12289);
    loaded = openlf2::load_packages(roots);
    assert(!loaded && loaded.error().code == openlf2::ErrorCode::limit);
    std::cout << "PASS: accepts 4096 total package assets and rejects 4097\n";
}
