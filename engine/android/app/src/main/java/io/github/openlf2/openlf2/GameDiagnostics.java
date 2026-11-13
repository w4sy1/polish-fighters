package io.github.openlf2.openlf2;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.AlertDialog;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/** Bounded, private, offline reports. Sharing happens only from the user's button. */
final class GameDiagnostics {
    private static boolean installed;
    private static final int LIMIT = 65536;
    static String redact(String text) {
        return text.replaceAll("https?://\\S+", "[URL]")
            .replaceAll("(?i)(token|password|secret|authorization)(\\s*[:=]\\s*)\\S+", "$1$2[REDACTED]")
            .replaceAll("(?i)Bearer\\s+\\S+", "Bearer [REDACTED]");
    }
    static void write(Context context, String name, String text) {
        File directory = new File(context.getFilesDir(), "diagnostics");
        if (!directory.isDirectory() && !directory.mkdirs()) return;
        AtomicFile file = new AtomicFile(new File(directory, name));
        FileOutputStream output = null;
        try {
            output = file.startWrite();
            String safe = redact(text);
            output.write(safe.substring(0, Math.min(LIMIT, safe.length())).getBytes(StandardCharsets.UTF_8));
            file.finishWrite(output);
        } catch (Exception error) { if (output != null) file.failWrite(output); }
    }
    static synchronized void install(Context context) {
        if (installed) return;
        installed = true;
        Context app = context.getApplicationContext();
        Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
            try {
                StringWriter stack = new StringWriter(); error.printStackTrace(new PrintWriter(stack));
                write(app, "java-last.txt", header(app) + "\n" + stack);
            } finally {
                if (previous != null) previous.uncaughtException(thread, error);
                else { android.os.Process.killProcess(android.os.Process.myPid()); System.exit(10); }
            }
        });
        if (Build.VERSION.SDK_INT >= 30) collectExit(app);
    }
    private static String header(Context context) {
        String version = "unknown";
        try { version = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName; }
        catch (Exception ignored) { /* Metadata is optional during a crash. */ }
        return "Polish Little Fighters " + version + "\nAndroid " + Build.VERSION.RELEASE
            + " / SDK " + Build.VERSION.SDK_INT + "\nDevice: " + Build.MANUFACTURER + " " + Build.MODEL;
    }
    @android.annotation.TargetApi(30)
    private static void collectExit(Context context) {
        try {
            ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            for (ApplicationExitInfo exit : manager.getHistoricalProcessExitReasons(null, 0, 4)) {
                int reason = exit.getReason();
                if (reason != ApplicationExitInfo.REASON_CRASH && reason != ApplicationExitInfo.REASON_CRASH_NATIVE
                    && reason != ApplicationExitInfo.REASON_ANR && reason != ApplicationExitInfo.REASON_LOW_MEMORY) continue;
                String trace = "";
                try (InputStream input = exit.getTraceInputStream()) {
                    if (input != null) trace = new String(readLimited(input), StandardCharsets.UTF_8);
                }
                write(context, "native-last.txt", header(context) + "\nTime: " + exit.getTimestamp()
                    + "\nReason: " + reason + "\nStatus: " + exit.getStatus()
                    + "\nPSS KiB: " + exit.getPss() + "\nRSS KiB: " + exit.getRss() + "\n" + trace);
                break;
            }
        } catch (Exception ignored) { /* System traces are optional and may be unavailable. */ }
    }
    private static byte[] readLimited(InputStream input) throws java.io.IOException {
        java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        while (output.size() < LIMIT) {
            int count = input.read(buffer, 0, Math.min(buffer.length, LIMIT - output.size()));
            if (count < 0) break;
            output.write(buffer, 0, count);
        }
        return output.toByteArray();
    }
    static String report(Context context) {
        StringBuilder text = new StringBuilder(header(context));
        for (String name : new String[]{"java-last.txt", "native-last.txt", "native-return.txt", "launch-last.txt"}) {
            File file = new File(context.getFilesDir(), "diagnostics/" + name);
            if (file.isFile()) try (InputStream input = new FileInputStream(file)) {
                text.append("\n\n").append(name).append("\n").append(new String(readLimited(input), StandardCharsets.UTF_8));
            } catch (Exception ignored) { text.append("\nRaport niedostepny"); }
        }
        File config = new File(context.getFilesDir(), "settings/config.json");
        if (config.isFile() && config.length() <= 1024 * 1024) try {
            byte[] bytes = new byte[(int) config.length()];
            try (InputStream input = new FileInputStream(config)) {
                int offset = 0;
                while (offset < bytes.length) {
                    int count = input.read(bytes, offset, bytes.length - offset);
                    if (count < 0) break;
                    offset += count;
                }
            }
            String source = new String(bytes, StandardCharsets.UTF_8);
            JSONObject document = new JSONObject(source);
            for (String key : new String[]{"polish_fighters_last_crash", "polish_fighters_last_session"}) {
                JSONObject value = document.optJSONObject(key);
                if (value != null) text.append("\n\n").append(key).append("\n").append(value.toString(2));
            }
        } catch (Exception ignored) { text.append("\nNie mozna odczytac kontekstu gry"); }
        return redact(text.toString());
    }
    static void show(Activity activity) {
        String text = report(activity);
        android.widget.TextView view = new android.widget.TextView(activity);
        view.setText(text); view.setTextIsSelectable(true); view.setPadding(20, 16, 20, 16);
        android.widget.ScrollView scroll = new android.widget.ScrollView(activity); scroll.addView(view);
        new AlertDialog.Builder(activity).setTitle("Diagnostyka / Diagnostics").setView(scroll)
            .setNegativeButton("Zamknij / Close", null)
            .setPositiveButton("Udostepnij / Share", (dialog, which) -> {
                Intent send = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text);
                try { activity.startActivity(Intent.createChooser(send, "Udostepnij raport")); }
                catch (android.content.ActivityNotFoundException ignored) { /* Report remains selectable locally. */ }
            }).show();
    }
}
