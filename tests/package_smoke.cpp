#include "openlf2/engine/packages.hpp"
#include <iostream>
#include <filesystem>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::filesystem::path scripts(argv[1]);
    const std::vector<std::filesystem::path> roots{scripts / "base", scripts / "polish-fighters"};
    auto loaded = openlf2::load_packages(roots);
    if (!loaded) { std::cerr << loaded.error().message << '\n'; return 1; }
    bool polish = false, roster = false, catalog = false;
    for (const auto& m : loaded->modules) {
        polish |= m.target == "base/i18n/polish";
        roster |= m.target == "polish-fighters/roster";
        catalog |= m.operation == "extend" && m.target == "base/game/catalog";
    }
    if (!polish || !roster || !catalog) return 3;
    std::cout << "PASS: native package loader, " << loaded->modules.size()
              << " declarations; Polish locale, roster and catalog decorator present\n";
}
