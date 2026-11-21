// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

// Android already reports native and Java crashes through GameDiagnostics (Java) and
// Application.getHistoricalProcessExitReasons(); the browser, Switch and Vita builds are out
// of scope for this feature. All three entry points are no-ops here so entry.cpp can call them
// unconditionally on every platform.
#include "openlf2/engine/crash_reporter.hpp"

namespace openlf2 {
void install_crash_handlers() {}
void report_previous_crash_if_any() {}
void mark_clean_shutdown() {}
}
