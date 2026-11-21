// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once
#include "openlf2/core/result.hpp"
#include <optional>
#include <string_view>

namespace openlf2 {
struct DiscordAttachment {
    std::string_view name;
    std::string_view text;
};
// Posts `content` (and, if given, a small text `attachment`) to a Discord webhook. `webhook_url`
// must be an HTTPS https://discord.com/api/webhooks/... or https://discordapp.com/api/webhooks/...
// URL; anything else is rejected before any network access, so a misconfigured or malicious
// URL cannot be used to send the report somewhere else. The caller is responsible for consent
// and for redacting `content`/`attachment` first (see openlf2/core/crash_report.hpp).
Result<void> send_discord_webhook(std::string_view webhook_url, std::string_view content,
                                  const std::optional<DiscordAttachment>& attachment);
}
