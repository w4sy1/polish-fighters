# Crash reporter (Discord webhook) -- 2026-11-22

Catches crashes and unclean shutdowns on Windows (and desktop Linux) and on Android, and offers
to send an anonymized report to a Discord channel through a webhook. Never automatic: the
player is always asked first, on the *next* launch, never from inside the crash itself.

## What exists today, before this change

- **Android** already had `GameDiagnostics.java`: an `UncaughtExceptionHandler` for Java crashes,
  `ApplicationExitInfo` for native (JNI) crashes and ANRs (API 30+), bounded local files under
  `diagnostics/`, and a manual "Diagnostyka / Diagnostics" viewer with a "Udostepnij / Share"
  button that hands the text to the OS share sheet. Nothing was sent anywhere automatically.
- **Windows / desktop C++** had no crash handler at all: no signal handlers, no
  `SetUnhandledExceptionFilter`, no `std::set_terminate`. `entry.cpp` only catches
  `std::exception` thrown during startup and shows a message box.
- Neither platform talked to Discord.

## Design

### Windows / Linux (new: `engine/src/adapters/sdl/crash_reporter.cpp`)

1. `install_crash_handlers()` runs first in `main()` (`entry.cpp`). It:
   - reads a small marker file (`crash-run-state.txt`, in the same per-user directory as
     `config.json`, see `settings_directory()`) left by the *previous* run. If it still says
     `"running"`, that run never reached a clean shutdown -- a crash, a kill, a hang.
   - overwrites it with `"running"` for *this* run, and installs signal handlers
     (`SIGSEGV`/`SIGABRT`/`SIGFPE`/`SIGILL`), a Windows `SetUnhandledExceptionFilter` (for
     access violations, which aren't delivered as a signal on MSVC) and `std::set_terminate`
     (uncaught C++ exceptions). Each writes a one-line `crash-last.txt` with whatever it knows
     (signal name, or the Windows exception code/address, or the exception's `what()`), then lets
     the OS finish the crash as normal (core dump / debugger).
2. `report_previous_crash_if_any()` runs right after, still before the game itself starts. If
   the previous run did not shut down cleanly **and** `OPENLF2_DISCORD_WEBHOOK_URL` is set **and**
   the player has not opted out, it shows a message box ("Tak" / "Nie" / "Nie pytaj wiecej") and
   only on "Tak" sends the report.
3. `mark_clean_shutdown()` runs when `run_application()` returns normally (success *or* an
   ordinary, already-handled failure) -- the next launch then has nothing to report.

The pure logic (anonymizing text, building the Discord message, the crash-loop guard) lives in
`engine/include/openlf2/core/crash_report.hpp` / `src/core/crash_report.cpp` -- no SDL, no curl,
no file I/O, so it is unit-tested directly (`tests/crash_report_test.cpp`, wired into
`tools/test_windows_native.ps1` the same way as the other native tests). The actual HTTPS POST
is `engine/src/adapters/curl/discord_webhook.cpp` (reuses the same libcurl/CA-bundle setup as
the existing account server client).

### Android (extends the existing `GameDiagnostics.java` with a new `CrashReporter.java`)

`GameBootstrapActivity` (the launcher activity) already calls `GameDiagnostics.install(this)`;
right after that it now also calls `CrashReporter.maybeReportPreviousCrash(this)`. If
`native-last.txt` or `java-last.txt` exists (GameDiagnostics already wrote it), a webhook URL is
configured, the player has not opted out, and this is not the exact same crash already handled,
it shows an `AlertDialog` with the same three choices and sends on "Tak" via a background
`HttpURLConnection` POST (JSON `{"content": ...}`).

## Privacy: what gets redacted

Both sides strip, before anything is ever assembled into a message:

- Windows/POSIX/macOS user-account path components (`C:\Users\<name>\...` ->
  `Users\[USER]\...`, `/home/<name>/...`, `/Users/<name>/...`), keeping the rest of the path.
- `token`/`password`/`secret`/`authorization` key/value pairs and `Bearer <token>`.
- Any bare `http(s)://` URL (which can carry a token in its query string) -> `[URL]`.

On Android this reuses the existing `GameDiagnostics.redact()` (already covered by
`GameDiagnosticsTest`); on Windows/Linux it is `openlf2::redact_sensitive()`
(`tests/crash_report_test.cpp`). Neither side ever includes `userdata/` (save files) or the
user's `config.json` secrets (account tokens) -- only the crash text itself (signal/exception
name, and on Android the existing bounded diagnostic files, which already exclude those).

## Consent, not silence

- The player is always asked, with a visible "Nie pytaj wiecej" (don't ask again) choice that is
  remembered (`crash-report-state.txt` on PC, `diagnostics/report-state.json` on Android).
- Nothing is configured by default: without `OPENLF2_DISCORD_WEBHOOK_URL` (PC) or a build-time
  webhook URL (Android, see below), the feature is entirely inert -- no dialog, no network call,
  not even a check. This also means a build with no webhook configured (most contributors'
  local builds) behaves exactly as before.

## Not spamming the channel (crash-loop guard)

A crash's *signature* is its first line with hex addresses normalized (`0x1234` -> `0xADDR`, so
ASLR does not defeat it). Whatever the player answers for a given signature -- yes, no, or don't
ask again -- that signature is remembered, and an identical one is never asked about or sent
again. A *different* crash (or the same one again after a different one happened in between) is
always offered again.

## Discord's 2000-character limit

`format_discord_message` (PC) keeps the whole report in Discord's `content` field when it fits;
otherwise it sends a short pointer message and the full (still redacted) text as a `.txt`
attachment via `multipart/form-data` (`payload_json` + `files[0]`, per Discord's webhook docs).
Android keeps things simpler: the message is truncated to fit `content` with a note pointing at
the in-game "Diagnostyka" viewer for the full text (no attachment upload) -- a deliberate
simplification, noted here rather than left silent.

## Configuring the webhook (never commit it)

- **Windows / Linux**: set the `OPENLF2_DISCORD_WEBHOOK_URL` environment variable before running
  the game (or in whatever launches CI/your dev build). Already covered by this repo's existing
  `.env` / `.env.*` gitignore pattern if you keep it in a local env file.
- **Android**: set the Gradle property `openlf2DiscordWebhookUrl`, e.g. a line in your own,
  **not committed**, `~/.gradle/gradle.properties` (never in `engine/android/gradle.properties`,
  which is tracked), or `-PopenlfDiscordWebhookUrl=...` on the command line. It becomes
  `BuildConfig.DISCORD_WEBHOOK_URL`.

Both sides also refuse to use anything but an `https://discord.com/api/webhooks/...` or
`https://discordapp.com/api/webhooks/...` URL, so a misconfigured value can never send a report
somewhere else.

## Verified so far / still to check

Verified in this sandbox (no Windows machine, no real Android device, no SDL3/Android-SDK
packages preinstalled here):

- `tests/crash_report_test.cpp` (redaction, Discord message formatting incl. the 2000-character
  attachment split, crash-loop signature dedupe) -- compiled and run directly with g++.
- `engine/src/adapters/curl/discord_webhook.cpp` -- compiled against the real libcurl, and its
  URL validation (rejects non-HTTPS and non-Discord hosts) exercised without any real network
  call.
- `engine/src/adapters/sdl/crash_reporter.cpp` -- compiled against a stand-in for the few SDL3
  declarations it uses (the real SDL3 headers are not installed here) and exercised end-to-end
  (install/crash/next-launch/dedupe state machine) against a stand-in `settings_directory()`.
  The real SDL3 struct layout and the real Windows SEH path could not be compiled here.
- `CrashReporter.java`'s pure logic (signature, crash-loop dedupe, Discord content
  truncation, webhook URL validation) -- compiled against the real Android 35 SDK `android.jar`
  and run with plain JUnit (`CrashReporterTest.java`, 7/7 pass).
- `python3 tools/test_lua_scripts.py` -- unaffected, still green (this change touches no Lua).

**Still needs checking on a real build** (this sandbox has no Windows toolchain and the Android
project's launcher icon, like its native libraries, is produced by `dist/build-android.sh`,
which needs the Android NDK and was not run here):

- `tools/test_windows_native.ps1`'s new `crash-report-test` case, with the real MSVC compiler.
- A full `./gradlew testDebugUnitTest lintDebug`, once the native/asset build has run.
- An actual end-to-end send: set `OPENLF2_DISCORD_WEBHOOK_URL` (or the Gradle property), force a
  crash (e.g. a debug-only "crash now" trigger, or just `kill -SEGV` the running process), relaunch,
  and confirm the message (and, for a long one, the attachment) arrives in the Discord channel.
