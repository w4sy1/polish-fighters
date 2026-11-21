#include "openlf2/core/crash_report.hpp"
#include <cassert>
#include <iostream>
int main() {
    // Secrets and bearer tokens are redacted, keys kept.
    {
        auto text = openlf2::redact_sensitive(
            "token: private password=hidden Authorization: Bearer sensitive https://example.test/?secret=one");
        assert(text.find("private") == std::string::npos);
        assert(text.find("hidden") == std::string::npos);
        assert(text.find("sensitive") == std::string::npos);
        assert(text.find("example.test") == std::string::npos);
        assert(text.find("token:") != std::string::npos);
    }
    // Windows and POSIX user-account path components are replaced, the rest of the path kept.
    {
        auto windows = openlf2::redact_sensitive(R"(C:\Users\Dominik\AppData\Roaming\OpenLF2\config.json)");
        assert(windows.find("Dominik") == std::string::npos);
        assert(windows.find("AppData") != std::string::npos);
        assert(windows.find("config.json") != std::string::npos);

        auto posix = openlf2::redact_sensitive("/home/dominik/.local/share/openlf2/config.json");
        assert(posix.find("dominik") == std::string::npos);
        assert(posix.find("config.json") != std::string::npos);

        auto macos = openlf2::redact_sensitive("/Users/dominik/Library/Application Support/openlf2");
        assert(macos.find("/Users/dominik") == std::string::npos);
    }
    // A short report fits entirely in Discord's message content.
    {
        openlf2::CrashEvent event{"OpenLF2 1.14.0 (abc1234)", "windows", "2026-11-22T03:14:00Z",
                                  "SIGSEGV at 0x7ffabc12", "frame=120 scene=duel"};
        auto message = openlf2::format_discord_message(event);
        assert(!message.has_attachment);
        assert(message.content.find("SIGSEGV") != std::string::npos);
        assert(message.content.find("windows") != std::string::npos);
        assert(message.content.find("duel") != std::string::npos);
        assert(message.content.size() <= 2000);
    }
    // A long report goes as an attachment with a short pointer message, both under the limit.
    {
        openlf2::CrashEvent event{"OpenLF2 1.14.0 (abc1234)", "windows", "2026-11-22T03:14:00Z",
                                  "SIGSEGV at 0x7ffabc12", std::string(4000, 'x')};
        auto message = openlf2::format_discord_message(event);
        assert(message.has_attachment);
        assert(message.attachment_name == "crash-report.txt");
        assert(message.attachment_text.size() > 2000);
        assert(message.content.size() <= 2000);
        assert(message.attachment_text.find("SIGSEGV") != std::string::npos);
    }
    // A report's own path/secret text is redacted even when it ends up in the attachment.
    {
        openlf2::CrashEvent event{"OpenLF2 1.14.0 (abc1234)", "windows", "2026-11-22T03:14:00Z",
                                  "SIGSEGV at 0x1",
                                  R"(C:\Users\Dominik\save.dat)" + std::string(2500, '.')};
        auto message = openlf2::format_discord_message(event);
        assert(message.has_attachment);
        assert(message.attachment_text.find("Dominik") == std::string::npos);
    }
    // The same crash (same normalized signature) twice in a row is suppressed; a different one,
    // or the same one again after a different one, is not.
    {
        openlf2::CrashEvent first{"", "windows", "", "SIGSEGV at 0x1111", ""};
        openlf2::CrashEvent again_same_address{"", "windows", "", "SIGSEGV at 0x1111", ""};
        openlf2::CrashEvent again_different_address{"", "windows", "", "SIGSEGV at 0x2222", ""};
        openlf2::CrashEvent other{"", "windows", "", "SIGABRT", ""};

        auto signature_first = openlf2::crash_signature(first);
        assert(openlf2::should_send_report("", signature_first));

        auto signature_repeat = openlf2::crash_signature(again_same_address);
        assert(signature_repeat == signature_first); // addresses normalize to the same signature
        assert(!openlf2::should_send_report(signature_first, signature_repeat));

        auto signature_moved = openlf2::crash_signature(again_different_address);
        assert(signature_moved == signature_first); // 0xADDR normalization collapses both
        assert(!openlf2::should_send_report(signature_first, signature_moved));

        auto signature_other = openlf2::crash_signature(other);
        assert(openlf2::should_send_report(signature_first, signature_other));
        assert(openlf2::should_send_report(signature_other, signature_first));
    }
    std::cout << "PASS: crash_report redaction, Discord formatting and crash-loop dedupe\n";
}
