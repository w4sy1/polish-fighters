package io.github.openlf2.openlf2;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.regex.Pattern;
import org.json.JSONObject;

/**
 * Offers to send an anonymized crash report to Discord, once, on the launch *after* a crash
 * that {@link GameDiagnostics} already recorded (native-last.txt / java-last.txt). Never
 * automatic: the player must say yes in the dialog, and can say "don't ask again". Whatever
 * the player answers, the same crash is not asked about (or sent) a second time -- the whole
 * point is to survive a crash loop without nagging the player or spamming the webhook.
 */
final class CrashReporter {
    // Headroom under Discord's 2000-character message content limit.
    private static final int CONTENT_LIMIT = 1900;
    private static final Pattern ADDRESS = Pattern.compile("0[xX][0-9a-fA-F]+");

    private CrashReporter() {}

    /** A short, stable fingerprint of a crash report's first line, used for the loop guard. */
    static String signature(String text) {
        String firstLine = text.split("\n", 2)[0];
        return ADDRESS.matcher(GameDiagnostics.redact(firstLine)).replaceAll("0xADDR");
    }

    static boolean shouldSend(String lastSignature, String signature) {
        return !signature.equals(lastSignature);
    }

    /** Rejects anything but an HTTPS Discord webhook URL, so a misconfigured value cannot send
     * the report somewhere else. */
    static boolean isDiscordWebhookUrl(String url) {
        return url != null && (url.startsWith("https://discord.com/api/webhooks/")
            || url.startsWith("https://discordapp.com/api/webhooks/"));
    }

    /** The redacted message to send, trimmed to fit Discord's content limit. */
    static String content(String header, String text) {
        String redacted = GameDiagnostics.redact(header + "\n" + text);
        if (redacted.length() <= CONTENT_LIMIT) return redacted;
        return redacted.substring(0, CONTENT_LIMIT) + "\n... (obciete; pelny raport w grze: Diagnostyka)";
    }

    private static String pendingCrashText(Context context) {
        for (String name : new String[]{"native-last.txt", "java-last.txt"}) {
            File file = new File(context.getFilesDir(), "diagnostics/" + name);
            if (!file.isFile()) continue;
            try (InputStream input = new FileInputStream(file)) {
                byte[] bytes = new byte[(int) Math.min(file.length(), 8192)];
                int read = input.read(bytes);
                if (read > 0) return new String(bytes, 0, read, StandardCharsets.UTF_8);
            } catch (Exception ignored) { /* try the next candidate */ }
        }
        return null;
    }

    private static File stateFile(Context context) {
        return new File(context.getFilesDir(), "diagnostics/report-state.json");
    }

    private static JSONObject loadState(Context context) {
        try {
            return new JSONObject(new String(Files.readAllBytes(stateFile(context).toPath()), StandardCharsets.UTF_8));
        } catch (Exception ignored) {
            return new JSONObject();
        }
    }

    private static void saveState(Context context, boolean optOut, String lastSignature) {
        try {
            JSONObject state = new JSONObject();
            state.put("opt_out", optOut);
            state.put("last_signature", lastSignature);
            File file = stateFile(context);
            File directory = file.getParentFile();
            if (directory != null) directory.mkdirs();
            Files.write(file.toPath(), state.toString().getBytes(StandardCharsets.UTF_8));
        } catch (Exception ignored) { /* best-effort; a failed save only means asking again later */ }
    }

    /** Call once, early in an activity's onCreate, after {@link GameDiagnostics#install}. */
    static void maybeReportPreviousCrash(Activity activity) {
        String webhookUrl = BuildConfig.DISCORD_WEBHOOK_URL;
        if (!isDiscordWebhookUrl(webhookUrl)) return; // not configured, or not a Discord webhook
        Context app = activity.getApplicationContext();
        String text = pendingCrashText(app);
        if (text == null) return; // nothing to report

        JSONObject state = loadState(app);
        if (state.optBoolean("opt_out", false)) return;
        String lastSignature = state.optString("last_signature", "");
        String signature = signature(text);
        if (!shouldSend(lastSignature, signature)) return;

        String header = "Polish Little Fighters / Android " + android.os.Build.VERSION.RELEASE
            + " / " + android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL;
        String message = content(header, text);

        new AlertDialog.Builder(activity)
            .setTitle("Blad / Error")
            .setMessage("Gra nie zamknela sie poprawnie przy poprzednim uruchomieniu.\n"
                + "Wyslac anonimowy raport o bledzie na Discord, aby pomoc go naprawic?")
            .setPositiveButton("Tak", (dialog, which) -> {
                sendAsync(webhookUrl, message);
                saveState(app, false, signature);
            })
            .setNegativeButton("Nie", (dialog, which) -> saveState(app, false, signature))
            .setNeutralButton("Nie pytaj wiecej", (dialog, which) -> saveState(app, true, signature))
            .show();
    }

    private static void sendAsync(String webhookUrl, String content) {
        new Thread(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("content", content);
                byte[] payload = body.toString().getBytes(StandardCharsets.UTF_8);
                URL url = new URL(webhookUrl);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                try {
                    connection.setRequestMethod("POST");
                    connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                    connection.setConnectTimeout(10000);
                    connection.setReadTimeout(15000);
                    connection.setDoOutput(true);
                    try (OutputStream out = connection.getOutputStream()) {
                        out.write(payload);
                    }
                    connection.getResponseCode(); // drains the response; a bad status is not fatal
                } finally {
                    connection.disconnect();
                }
            } catch (Exception ignored) { /* best-effort: a failed report must never crash the game */ }
        }).start();
    }
}
