// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once
#include "openlf2/core/result.hpp"
#include <string_view>

namespace openlf2 {
// Sends a player-written bug report -- typed into the credits menu's "ZGŁOŚ BŁĄD (DISCORD)"
// screen (engine/scripts/polish-fighters/bug_report_screen.lua), next to the existing e-mail
// based "report_bug" action -- to the project's Discord webhook. This deliberately reuses the
// automatic crash reporter's own message formatting and redaction (openlf2/core/crash_report.hpp)
// so a manual report and an automatic crash report are built the same way, and the same
// webhook-URL validation (openlf2/ports/discord_webhook.hpp): there is exactly one code path in
// this engine that talks to Discord.
//
// `text` is the player's own words; it is redacted before sending (see redact_sensitive) but not
// otherwise validated here -- the caller should reject an empty/whitespace-only report first.
// Like the crash reporter, the webhook URL is never hardcoded: it comes from the
// OPENLF2_DISCORD_WEBHOOK_URL environment variable (set directly on desktop; set from
// BuildConfig.DISCORD_WEBHOOK_URL via android.system.Os.setenv before the native engine starts
// on Android -- see OpenLF2Activity.main()). Missing configuration is reported as an error, not
// silently swallowed.
Result<void> submit_bug_report(std::string_view text);
}
