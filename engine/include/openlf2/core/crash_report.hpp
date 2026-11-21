// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once
#include <string>
#include <string_view>

namespace openlf2 {
// Replaces text that could identify the player before a report leaves the machine: Windows and
// POSIX home-directory user names found in file paths, "key: value" / "key=value" secrets
// (token, password, secret, authorization), bearer tokens, and bare URLs (which can carry a
// token in their query string). Mirrors GameDiagnostics.redact on Android so a report reads the
// same on every platform. Never throws.
std::string redact_sensitive(std::string_view text);

// One crash, or a previous run that did not shut down cleanly.
struct CrashEvent {
    std::string build_label;   // OPENLF2_BUILD_LABEL, e.g. "OpenLF2 1.14.0 (abc1234)"
    std::string platform;      // "windows", "linux", "macos", ...
    std::string timestamp_utc; // ISO 8601, e.g. "2026-11-22T03:14:00Z"
    std::string summary;       // one line, e.g. "SIGSEGV at 0x1234" or "previous run did not exit cleanly"
    std::string details;       // optional extra text (stack/context); may be empty, not yet redacted
};

// Discord's message `content` field is capped at 2000 characters (Discord webhook API); a
// report that does not fit goes as a small text-file attachment instead, with a short pointer
// message. `format_discord_message` redacts `event.summary` and `event.details` itself -- callers
// must not redact them beforehand (doing so twice is harmless, but unnecessary).
struct DiscordMessage {
    std::string content;
    bool has_attachment = false;
    std::string attachment_name; // only meaningful when has_attachment
    std::string attachment_text; // only meaningful when has_attachment
};

// Builds the message to send for `event`. Never throws.
DiscordMessage format_discord_message(const CrashEvent& event);

// A short, stable fingerprint for `event`, used to avoid re-sending the exact same report over
// and over during a crash loop. Hexadecimal addresses in the summary are normalized first, so
// two otherwise-identical crashes at different addresses (ASLR) still collapse to one signature.
std::string crash_signature(const CrashEvent& event);

// Whether a crash with `signature` should be sent, given the signature that was last sent
// (empty if none has been sent yet). A signature identical to the last one sent is suppressed;
// this is the whole of the crash-loop guard -- a different crash, or the same crash again after
// a different one, is always offered to the player again.
bool should_send_report(std::string_view last_sent_signature, std::string_view signature);
}
