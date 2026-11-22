// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#include "openlf2/engine/bug_report.hpp"
#include "openlf2/core/crash_report.hpp"
#include "openlf2/ports/discord_webhook.hpp"
#include "openlf2_build_info.hpp"
#include <cstdlib>
#include <ctime>
#include <string>

namespace openlf2 {
#ifndef __EMSCRIPTEN__
namespace {
// __ANDROID__ must be checked before __linux__: the Android NDK toolchain defines both, and a
// manual report sent from the Android build should say so rather than reading "linux".
std::string current_platform_name() {
#if defined(__ANDROID__)
    return "android";
#elif defined(_WIN32)
    return "windows";
#elif defined(__APPLE__)
    return "macos";
#elif defined(__linux__)
    return "linux";
#else
    return "unknown";
#endif
}

std::string current_timestamp_utc() {
    const auto now = std::time(nullptr);
    std::tm utc{};
#ifdef _WIN32
    gmtime_s(&utc, &now);
#else
    gmtime_r(&now, &utc);
#endif
    char buffer[32];
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &utc);
    return buffer;
}
}
#endif

Result<void> submit_bug_report(std::string_view text) {
#ifdef __EMSCRIPTEN__
    // The web build never links the curl-based discord_webhook.cpp (see engine/CMakeLists.txt's
    // OPENLF2_DEPENDENCY_PROVIDER == "web" branch), so this must not reach send_discord_webhook.
    (void)text;
    return fail(ErrorCode::unsupported, "Zglaszanie bledow na Discord jest niedostepne w tej wersji.");
#else
    const char* webhook_env = std::getenv("OPENLF2_DISCORD_WEBHOOK_URL");
    if (webhook_env == nullptr || *webhook_env == '\0') {
        return fail(ErrorCode::io, "Brak konfiguracji webhooka Discord (OPENLF2_DISCORD_WEBHOOK_URL).");
    }
    const CrashEvent event{OPENLF2_BUILD_LABEL, current_platform_name(), current_timestamp_utc(),
                            "Zgloszenie bledu od gracza (wyslane recznie z menu TWORCY)", std::string(text)};
    const auto message = format_discord_message(event);
    if (message.has_attachment) {
        const DiscordAttachment attachment{message.attachment_name, message.attachment_text};
        return send_discord_webhook(webhook_env, message.content, attachment);
    }
    return send_discord_webhook(webhook_env, message.content, std::nullopt);
#endif
}
}
