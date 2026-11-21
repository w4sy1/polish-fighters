// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#include "openlf2/core/crash_report.hpp"
#include <algorithm>
#include <cctype>
#include <regex>

namespace openlf2 {
namespace {
// A conservative stand-in for "a path component that names a user account": letters, digits,
// space, dot, underscore and hyphen, stopping at the next path separator.
constexpr auto account_name_pattern = R"([^\\/:*?"<>|\r\n]+)";

std::string redact_paths(std::string text) {
    // Windows: C:\Users\<name>\... and \Users\<name>\... (UNC-free; good enough for crash text).
    static const std::regex windows_user(std::string(R"((?:[A-Za-z]:)?[\\]Users[\\])") + account_name_pattern,
                                          std::regex::icase);
    text = std::regex_replace(text, windows_user, "Users\\[USER]");
    // POSIX: /home/<name>/... and macOS /Users/<name>/...
    static const std::regex posix_home(std::string(R"(/home/)") + account_name_pattern);
    text = std::regex_replace(text, posix_home, "/home/[USER]");
    static const std::regex macos_home(std::string(R"(/Users/)") + account_name_pattern);
    text = std::regex_replace(text, macos_home, "/Users/[USER]");
    return text;
}

std::string redact_secrets(std::string text) {
    // Bearer tokens first: "Authorization: Bearer xyz" would otherwise have its value eaten by
    // the generic key/value rule below (stopping at the first space, right after "Bearer").
    static const std::regex bearer(R"(Bearer\s+\S+)", std::regex::icase);
    text = std::regex_replace(text, bearer, "Bearer [REDACTED]");
    // "token: value", "password=value", "Authorization: value", stopping at whitespace.
    static const std::regex key_value(R"((token|password|secret|authorization)(\s*[:=]\s*)\S+)",
                                      std::regex::icase);
    text = std::regex_replace(text, key_value, "$1$2[REDACTED]");
    static const std::regex url(R"(https?://\S+)");
    text = std::regex_replace(text, url, "[URL]");
    return text;
}
}

std::string redact_sensitive(std::string_view text) {
    return redact_secrets(redact_paths(std::string(text)));
}

namespace {
constexpr std::size_t discord_content_limit = 2000;

std::string build_header(const CrashEvent& event) {
    std::string header;
    header += event.build_label;
    header += " / ";
    header += event.platform;
    header += " / ";
    header += event.timestamp_utc;
    return header;
}
}

DiscordMessage format_discord_message(const CrashEvent& event) {
    CrashEvent clean = event;
    clean.summary = redact_sensitive(event.summary);
    clean.details = redact_sensitive(event.details);

    std::string full = "**OpenLF2 crash report**\n" + build_header(clean) + "\n" + clean.summary;
    if (!clean.details.empty()) full += "\n\n" + clean.details;

    DiscordMessage message;
    if (full.size() <= discord_content_limit) {
        message.content = std::move(full);
        return message;
    }
    message.has_attachment = true;
    message.attachment_name = "crash-report.txt";
    message.attachment_text = std::move(full);
    std::string pointer = "**OpenLF2 crash report**\n" + build_header(clean) + "\n" + clean.summary;
    if (pointer.size() > discord_content_limit) pointer.resize(discord_content_limit);
    pointer += "\n(full report attached)";
    if (pointer.size() > discord_content_limit) pointer.resize(discord_content_limit);
    message.content = std::move(pointer);
    return message;
}

std::string crash_signature(const CrashEvent& event) {
    static const std::regex address(R"(0[xX][0-9a-fA-F]+)");
    return std::regex_replace(redact_sensitive(event.summary), address, "0xADDR");
}

bool should_send_report(std::string_view last_sent_signature, std::string_view signature) {
    return signature != last_sent_signature;
}
}
