// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once

namespace openlf2 {
// Installs the operating system's crash hooks (signal handlers; on Windows also a structured
// exception filter and std::set_terminate) as early as possible in main(), before anything
// else runs. Also notices whether the *previous* run shut down cleanly, for
// report_previous_crash_if_any() to use later. Writes only a small local file; never touches
// the network. No-op on platforms that already report native crashes through the OS or the
// Java layer (Android) or that this feature does not cover (consoles, the browser).
void install_crash_handlers();

// Call once, early in startup, after install_crash_handlers() and once the platform can show a
// message box. If the previous run did not shut down cleanly, and a Discord webhook is
// configured (the OPENLF2_DISCORD_WEBHOOK_URL environment variable) and the player has not
// opted out, asks for consent ("wystapil blad, wyslac raport?" with a "do not ask again"
// choice) and -- only on yes -- sends an anonymized report. A crash identical to the last one
// sent is not sent, or asked about, again (crash-loop guard). Best-effort: never throws, and
// every failure (no webhook configured, no network, no display to show a dialog on, player
// said no) is silent -- this must never get in the way of actually playing the game.
void report_previous_crash_if_any();

// Call right before returning normally from main(), after run_application() returns -- even
// with a non-zero exit code, as long as that is an ordinary, already-handled failure and not a
// crash. Marks this run as having shut down cleanly, so the next run does not treat it as one.
void mark_clean_shutdown();
}
