// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

// Windows and Linux desktop builds: catches native crashes (signals; on Windows also SEH) and
// unhandled C++ exceptions, and offers to send an anonymized report to Discord on the *next*
// launch -- never from inside the crash itself, which is too fragile a place to show a dialog
// or touch the network. See engine/include/openlf2/engine/crash_reporter.hpp.
//
// The signal handler below is best-effort, not strictly POSIX signal-safe (it uses buffered C
// stdio); that mirrors the rest of this codebase's pragmatic approach to crash-time code rather
// than a hard real-time guarantee, and the worst case is simply that no detail gets written --
// the player is still asked about a generic "did not close cleanly" report.
#include "openlf2/engine/crash_reporter.hpp"
#include "openlf2/core/crash_report.hpp"
#include "openlf2/ports/discord_webhook.hpp"
#include "openlf2/ports/platform.hpp"
#include "openlf2_build_info.hpp"
#include <SDL3/SDL.h>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif

namespace openlf2 {
namespace {
// Resolved once by install_crash_handlers(); plain strings so the signal handler never has to
// touch std::filesystem::path.
std::string g_run_marker_path;
std::string g_crash_detail_path;
std::string g_state_path;
bool g_paths_ready = false;
bool g_previous_run_crashed = false;
std::string g_previous_crash_detail;

void write_crash_detail_best_effort(const char* text) noexcept {
    if (g_crash_detail_path.empty()) return;
    std::FILE* file = std::fopen(g_crash_detail_path.c_str(), "w");
    if (file == nullptr) return;
    std::fputs(text, file);
    std::fclose(file);
}

const char* signal_name(int signal_number) {
    switch (signal_number) {
        case SIGABRT: return "SIGABRT";
        case SIGSEGV: return "SIGSEGV";
        case SIGFPE: return "SIGFPE";
        case SIGILL: return "SIGILL";
        default: return "unknown signal";
    }
}

extern "C" void handle_fatal_signal(int signal_number) {
    write_crash_detail_best_effort(signal_name(signal_number));
    // Restore the platform's default handling (core dump / debugger) once the detail is saved.
    std::signal(signal_number, SIG_DFL);
    std::raise(signal_number);
}

void handle_terminate() {
    std::string message = "unhandled C++ exception (std::terminate)";
    if (auto active = std::current_exception()) {
        try {
            std::rethrow_exception(active);
        } catch (const std::exception& error) {
            message += ": ";
            message += error.what();
        } catch (...) {
            message += ": (not a std::exception)";
        }
    }
    write_crash_detail_best_effort(message.c_str());
    std::abort();
}

#ifdef _WIN32
LONG WINAPI handle_windows_exception(EXCEPTION_POINTERS* info) {
    char buffer[160];
    const unsigned long code = (info != nullptr && info->ExceptionRecord != nullptr)
        ? info->ExceptionRecord->ExceptionCode : 0;
    const void* address = (info != nullptr && info->ExceptionRecord != nullptr)
        ? info->ExceptionRecord->ExceptionAddress : nullptr;
    std::snprintf(buffer, sizeof(buffer), "Windows exception 0x%08lX at %p", code, address);
    write_crash_detail_best_effort(buffer);
    return EXCEPTION_EXECUTE_HANDLER;
}
#endif

std::string current_platform_name() {
#ifdef _WIN32
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

// Plain "key=value" lines -- this file is internal only, never shown to the player, so it does
// not need the JSON machinery used for the user-facing configuration.
struct ReportState {
    bool opt_out = false;
    std::string last_signature;
};

ReportState load_report_state(const std::string& path) {
    ReportState state;
    std::ifstream in(path, std::ios::binary);
    std::string line;
    while (in && std::getline(in, line)) {
        if (line.rfind("opt_out=", 0) == 0) state.opt_out = line.substr(8) == "1";
        else if (line.rfind("last_signature=", 0) == 0) state.last_signature = line.substr(15);
    }
    return state;
}

void save_report_state(const std::string& path, const ReportState& state) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return;
    out << "opt_out=" << (state.opt_out ? "1" : "0") << "\n";
    out << "last_signature=" << state.last_signature << "\n";
}

enum class Consent { Yes, No, NeverAskAgain };

Consent ask_consent() {
    const SDL_MessageBoxButtonData buttons[] = {
        {SDL_MESSAGEBOX_BUTTON_RETURNKEY_DEFAULT, 1, "Tak"},
        {SDL_MESSAGEBOX_BUTTON_ESCAPEKEY_DEFAULT, 0, "Nie"},
        {0, 2, "Nie pytaj wiecej"},
    };
    const SDL_MessageBoxData data{
        SDL_MESSAGEBOX_WARNING,
        nullptr,
        "Polish Fighters",
        "Gra nie zamknela sie poprawnie przy poprzednim uruchomieniu.\n"
        "Wyslac anonimowy raport o bledzie na Discord, aby pomoc go naprawic?",
        3,
        buttons,
        nullptr,
    };
    int clicked = -1;
    if (!SDL_ShowMessageBox(&data, &clicked)) return Consent::No; // no display available: fail safe, never send
    switch (clicked) {
        case 1: return Consent::Yes;
        case 2: return Consent::NeverAskAgain;
        default: return Consent::No;
    }
}
}

void install_crash_handlers() {
    auto directory = settings_directory();
    if (!directory) return; // nowhere to write; skip the whole feature rather than guess a path
    std::error_code error;
    std::filesystem::create_directories(*directory, error);
    g_run_marker_path = (*directory / "crash-run-state.txt").string();
    g_crash_detail_path = (*directory / "crash-last.txt").string();
    g_state_path = (*directory / "crash-report-state.txt").string();
    g_paths_ready = true;

    // Read what the *previous* run left behind before this run overwrites it below.
    {
        std::ifstream marker(g_run_marker_path, std::ios::binary);
        std::string state;
        if (marker && std::getline(marker, state) && state == "running") {
            g_previous_run_crashed = true;
            std::ifstream detail(g_crash_detail_path, std::ios::binary);
            if (detail) {
                std::ostringstream buffer;
                buffer << detail.rdbuf();
                g_previous_crash_detail = buffer.str();
            }
        }
    }
    // This run starts now; until mark_clean_shutdown() runs, a future launch sees "running".
    {
        std::ofstream out(g_run_marker_path, std::ios::binary | std::ios::trunc);
        if (out) out << "running";
    }
    std::remove(g_crash_detail_path.c_str()); // stale detail from an even older run

    std::signal(SIGABRT, &handle_fatal_signal);
    std::signal(SIGSEGV, &handle_fatal_signal);
    std::signal(SIGFPE, &handle_fatal_signal);
    std::signal(SIGILL, &handle_fatal_signal);
    std::set_terminate(&handle_terminate);
#ifdef _WIN32
    SetUnhandledExceptionFilter(&handle_windows_exception);
#endif
}

void report_previous_crash_if_any() {
    if (!g_paths_ready || !g_previous_run_crashed) return;
    const char* webhook_env = std::getenv("OPENLF2_DISCORD_WEBHOOK_URL");
    if (webhook_env == nullptr || *webhook_env == '\0') return; // feature not configured
    const std::string webhook_url = webhook_env;

    auto state = load_report_state(g_state_path);
    if (state.opt_out) return;

    CrashEvent event;
    event.build_label = OPENLF2_BUILD_LABEL;
    event.platform = current_platform_name();
    event.timestamp_utc = current_timestamp_utc();
    event.summary = g_previous_crash_detail.empty() ? "Previous session did not close cleanly"
                                                     : g_previous_crash_detail;

    const auto signature = crash_signature(event);
    if (!should_send_report(state.last_signature, signature)) return; // same crash as last time

    const auto consent = ask_consent();
    // Whatever the player answers, this exact crash has now been handled: a "no" must not come
    // back and ask again on every single launch of a crash loop, any more than a "yes" should
    // resend. Only "don't ask again" additionally silences every future crash too.
    state.last_signature = signature;
    if (consent == Consent::NeverAskAgain) state.opt_out = true;
    save_report_state(g_state_path, state);
    if (consent != Consent::Yes) return;

    const auto message = format_discord_message(event);
    if (message.has_attachment) {
        const DiscordAttachment attachment{message.attachment_name, message.attachment_text};
        send_discord_webhook(webhook_url, message.content, attachment);
    } else {
        send_discord_webhook(webhook_url, message.content, std::nullopt);
    }
}

void mark_clean_shutdown() {
    if (!g_paths_ready) return;
    std::ofstream out(g_run_marker_path, std::ios::binary | std::ios::trunc);
    if (out) out << "closed";
}
}
