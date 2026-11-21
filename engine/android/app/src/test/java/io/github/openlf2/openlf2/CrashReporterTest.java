package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import org.junit.Test;

/**
 * Pure-logic tests for {@link CrashReporter}: no Activity, no dialog, no network -- exactly
 * the part of this feature that does not need a real device or a real webhook to verify.
 */
public class CrashReporterTest {
    @Test public void sameCrashTwiceHasTheSameSignature() {
        String first = CrashReporter.signature("SIGSEGV at 0x7ffabc12\nmore detail");
        String again = CrashReporter.signature("SIGSEGV at 0x7ffabc12\nunrelated other detail");
        assertEquals(first, again);
    }

    @Test public void addressesAreNormalizedSoAslrDoesNotDefeatTheLoopGuard() {
        String a = CrashReporter.signature("SIGSEGV at 0x1111");
        String b = CrashReporter.signature("SIGSEGV at 0x2222");
        assertEquals(a, b);
        assertTrue(a.contains("0xADDR"));
    }

    @Test public void differentSignalsHaveDifferentSignatures() {
        String segv = CrashReporter.signature("SIGSEGV at 0x1");
        String abrt = CrashReporter.signature("SIGABRT");
        assertNotEquals(segv, abrt);
    }

    @Test public void identicalSignatureIsSuppressedButAnyChangeIsNot() {
        String signature = CrashReporter.signature("SIGSEGV at 0x1");
        assertFalse(CrashReporter.shouldSend(signature, signature));
        assertTrue(CrashReporter.shouldSend("", signature));
        assertTrue(CrashReporter.shouldSend(CrashReporter.signature("SIGABRT"), signature));
    }

    @Test public void contentIsRedactedAndCapped() {
        String message = CrashReporter.content("header",
            "token: private " + new String(new char[3000]).replace('\0', 'x'));
        assertFalse(message.contains("private"));
        assertTrue(message.length() <= 2000);
        assertTrue(message.contains("obciete"));
    }

    @Test public void shortContentIsNotTruncated() {
        String message = CrashReporter.content("header", "short crash text");
        assertTrue(message.contains("short crash text"));
        assertFalse(message.contains("obciete"));
    }

    @Test public void onlyRealDiscordWebhookUrlsAreAccepted() {
        assertTrue(CrashReporter.isDiscordWebhookUrl("https://discord.com/api/webhooks/1/token"));
        assertTrue(CrashReporter.isDiscordWebhookUrl("https://discordapp.com/api/webhooks/1/token"));
        assertFalse(CrashReporter.isDiscordWebhookUrl(null));
        assertFalse(CrashReporter.isDiscordWebhookUrl(""));
        assertFalse(CrashReporter.isDiscordWebhookUrl("http://discord.com/api/webhooks/1/token"));
        assertFalse(CrashReporter.isDiscordWebhookUrl("https://evil.example/api/webhooks/1/token"));
    }
}
