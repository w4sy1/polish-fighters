// Standalone compile/run check for openlf2::submit_bug_report's glue logic (env-var lookup and
// delegation into the already-tested crash_report/discord_webhook code). No network access is
// made or required: both paths exercised here fail before any HTTP request is attempted.
#include "openlf2/engine/bug_report.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>

int main() {
    // 1. No webhook configured at all.
#ifdef _WIN32
    _putenv_s("OPENLF2_DISCORD_WEBHOOK_URL", "");
#else
    unsetenv("OPENLF2_DISCORD_WEBHOOK_URL");
#endif
    {
        const auto result = openlf2::submit_bug_report("Gra sie crashuje po wejsciu do portalu.");
        assert(!result.has_value());
        assert(result.error().message.find("OPENLF2_DISCORD_WEBHOOK_URL") != std::string::npos);
    }

    // 2. Configured, but not a Discord webhook URL -- must be rejected by the same validation
    // the automatic crash reporter uses, before any network access.
#ifdef _WIN32
    _putenv_s("OPENLF2_DISCORD_WEBHOOK_URL", "https://evil.example.com/steal");
#else
    setenv("OPENLF2_DISCORD_WEBHOOK_URL", "https://evil.example.com/steal", 1);
#endif
    {
        const auto result = openlf2::submit_bug_report("Test message.");
        assert(!result.has_value());
    }

#ifdef _WIN32
    _putenv_s("OPENLF2_DISCORD_WEBHOOK_URL", "");
#else
    unsetenv("OPENLF2_DISCORD_WEBHOOK_URL");
#endif

    std::puts("bug_report_test: all assertions passed");
    return 0;
}
