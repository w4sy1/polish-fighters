// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once
#include "openlf2/core/result.hpp"
#include <atomic>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>

namespace openlf2 {
// Signed Polish Fighters mod catalogue on GitHub (mods/catalog.json + catalog.sig).
struct ModInstallProgress {
    std::atomic<std::uint64_t> received{0};
    std::atomic<std::uint64_t> total{0};
    std::atomic<int> phase{0}; // 0 idle, 1 downloading, 2 verifying, 3 unpacking
    std::atomic<std::uint32_t> files{0};
    std::atomic<bool> cancelled{false};
};
// Where the engine reads content packs; set by the application before scripts run.
void set_mod_content_directory(const std::filesystem::path& directory,
                               const std::filesystem::path& bundled_directory = {});
std::filesystem::path mod_content_directory();
std::optional<std::string> github_mod_receipt(std::string_view id);
// Downloads the catalogue and its Ed25519 signature; returns the verified JSON text.
Result<std::string> github_mod_catalogue();
// Installs `id` from a catalogue previously returned by github_mod_catalogue(). The envelope
// size and SHA-256 come from that catalogue; signatures inside the envelope are checked too.
Result<std::string> github_mod_install(std::string_view verified_catalogue, std::string_view id,
                                       ModInstallProgress& progress);
// File chosen by the Windows file picker, consumed once by the current mod browser.
void set_local_mod_file(const std::filesystem::path& file);
std::optional<std::filesystem::path> take_local_mod_file();
Result<std::string> import_signed_mod(const std::filesystem::path& file, ModInstallProgress& progress);
// True when this build can install mods itself (builds with libcurl and OpenSSL).
bool github_mods_supported() noexcept;
}
