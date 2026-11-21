package io.github.openlf2.openlf2;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Build;
import androidx.core.content.FileProvider;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;

final class GitHubUpdates {
    private static final String RELEASES = "https://github.com/w4sy1/polish-fighters/releases/";
    private static final String API = "https://api.github.com/repos/w4sy1/polish-fighters/releases?per_page=5";
    private static final int MAX_APK_BYTES = 1024 * 1024 * 1024;
    private static final Pattern VERSION = Pattern.compile("(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})");
    private static final Pattern CHECKSUM = Pattern.compile("^([0-9a-fA-F]{64})[ \\t]+\\*?(\\S+)\\s*$");

    static final class Candidate {
        final String version, name, apk, checksum;
        Candidate(String version, String name, String apk, String checksum) {
            this.version=version;
            this.name=name;
            this.apk=apk;
            this.checksum=checksum;
        }
    }

    static long version(String text) {
        Matcher m = VERSION.matcher(text == null ? "" : text);
        return m.find() ? Long.parseLong(m.group(1))*1000000L + Long.parseLong(m.group(2))*1000L
            + Long.parseLong(m.group(3)) : 0;
    }

    static Candidate select(String json, String installed, String[] abis) throws Exception {
        JSONArray releases = new JSONArray(json);
        long best = version(installed);
        Candidate result = null;
        for (int i=0; i<releases.length(); i++) {
            JSONObject release = releases.optJSONObject(i);
            if (release == null || release.optBoolean("draft") ||
                !release.optString("html_url").startsWith(RELEASES + "tag/")) continue;
            String available = release.optString("tag_name");
            if (version(available) == 0) available = release.optString("name");
            long candidate = version(available);
            if (candidate <= best) continue;
            JSONArray assets = release.optJSONArray("assets");
            for (String abi : abis) {
                if (!"arm64-v8a".equals(abi) && !"x86_64".equals(abi)) continue;
                String name = "PolishFighters-Android-" + abi + ".apk";
                String apk = asset(assets, name);
                String checksum = asset(assets, name + ".sha256");
                if (apk == null || !(apk + ".sha256").equals(checksum)) continue;
                result = new Candidate(available, name, apk, checksum);
                best = candidate;
                break;
            }
        }
        return result;
    }

    private static String asset(JSONArray assets, String name) {
        if (assets == null) return null;
        for (int i=0; i<assets.length(); i++) {
            JSONObject asset = assets.optJSONObject(i);
            if (asset == null || !name.equals(asset.optString("name")) ||
                !"uploaded".equals(asset.optString("state"))) continue;
            String link = asset.optString("browser_download_url");
            if (link.matches(Pattern.quote(RELEASES + "download/") + "[A-Za-z0-9_.-]+/" + Pattern.quote(name))) return link;
        }
        return null;
    }

    static void check(Activity activity) {
        run(activity, "Sprawdzam aktualizacje…", cancelled -> {
            PackageInfo installed = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
            Candidate candidate = select(read(API, 512 * 1024, cancelled), installed.versionName, Build.SUPPORTED_ABIS);
            return () -> {
                if (candidate == null) {
                    message(activity, "Aktualizacja gry", "Zainstalowana wersja " + installed.versionName +
                        ". Brak nowszej paczki dla tego urządzenia.");
                    return;
                }
                new AlertDialog.Builder(activity).setTitle("Dostępna aktualizacja")
                    .setMessage("Masz " + installed.versionName + " · Dostępna " + candidate.version +
                        "\nPo weryfikacji telefon otworzy instalator.")
                    .setPositiveButton("Pobierz", (dialog, which) -> download(activity, candidate))
                    .setNegativeButton("Później", null).show();
            };
        });
    }

    private static void download(Activity activity, Candidate candidate) {
        run(activity, "Pobieram i sprawdzam APK…", cancelled -> {
            Matcher checksum = CHECKSUM.matcher(read(candidate.checksum, 1024, cancelled));
            if (!checksum.matches() || !candidate.name.equals(checksum.group(2))) {
                throw new IOException("Nieprawidłowy plik SHA-256 wydania.");
            }
            File directory = new File(activity.getCacheDir(), "verified-updates");
            if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("Brak katalogu aktualizacji.");
            File apk = File.createTempFile("polish-fighters-", ".apk", directory);
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            boolean verified = false;
            try {
                HttpURLConnection connection = connect(candidate.apk);
                try (InputStream input = connection.getInputStream(); FileOutputStream output = new FileOutputStream(apk)) {
                    byte[] bytes = new byte[65536];
                    int count, total = 0;
                    while ((count = input.read(bytes)) != -1) {
                        total += count;
                        if (cancelled.get() || total > MAX_APK_BYTES) throw new IOException("Przerwano pobieranie APK.");
                        digest.update(bytes, 0, count);
                        output.write(bytes, 0, count);
                    }
                } finally { connection.disconnect(); }
                StringBuilder hex = new StringBuilder(64);
                for (byte value : digest.digest()) hex.append(String.format(Locale.ROOT, "%02x", value & 255));
                if (!hex.toString().equalsIgnoreCase(checksum.group(1))) throw new IOException("Niezgodna suma SHA-256 APK.");
                verifyPackage(activity, apk);
                verified = !cancelled.get();
            } finally {
                if (!verified) apk.delete();
            }
            return () -> {
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setDataAndType(FileProvider.getUriForFile(activity,
                    activity.getPackageName() + ".updates", apk), "application/vnd.android.package-archive");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                try { activity.startActivity(intent); }
                catch (RuntimeException error) { message(activity, "Aktualizacja gry", "Systemowy instalator jest niedostępny."); }
            };
        });
    }

    @SuppressWarnings("deprecation")
    private static void verifyPackage(Activity activity, File file) throws Exception {
        PackageManager packages = activity.getPackageManager();
        int flags = Build.VERSION.SDK_INT >= 28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES;
        PackageInfo installed = packages.getPackageInfo(activity.getPackageName(), flags);
        PackageInfo update = packages.getPackageArchiveInfo(file.getAbsolutePath(), flags);
        if (update == null || !installed.packageName.equals(update.packageName)) {
            throw new IOException("APK ma inny identyfikator aplikacji.");
        }
        long current = Build.VERSION.SDK_INT >= 28 ? installed.getLongVersionCode() : installed.versionCode;
        long available = Build.VERSION.SDK_INT >= 28 ? update.getLongVersionCode() : update.versionCode;
        if (available <= current) throw new IOException("APK nie ma wyższego numeru kompilacji.");
        Signature[] previous = Build.VERSION.SDK_INT >= 28
            ? installed.signingInfo == null ? null : installed.signingInfo.getApkContentsSigners() : installed.signatures;
        Signature[] incoming = Build.VERSION.SDK_INT >= 28
            ? update.signingInfo == null ? null : update.signingInfo.getApkContentsSigners() : update.signatures;
        if (previous == null || previous.length == 0 || incoming == null || incoming.length != previous.length ||
            !Arrays.asList(incoming).containsAll(Arrays.asList(previous))) {
            throw new IOException("Certyfikat APK nie odpowiada zainstalowanej grze.");
        }
    }

    private static HttpURLConnection connect(String address) throws IOException {
        URL url = new URL(address);
        for (int hop=0; hop<5; hop++) {
            String host = url.getHost();
            if (!"https".equals(url.getProtocol()) || url.getUserInfo() != null ||
                !("api.github.com".equals(host) || "github.com".equals(host) ||
                  "release-assets.githubusercontent.com".equals(host) || "objects.githubusercontent.com".equals(host))) {
                throw new IOException("Nieznane źródło aktualizacji.");
            }
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(10000);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestProperty("User-Agent", "PolishFighters-UpdateCheck/1");
            try {
                int status = connection.getResponseCode();
                if (status == 200) return connection;
                String location = connection.getHeaderField("Location");
                if (status < 300 || status >= 400 || location == null) throw new IOException("GitHub HTTP " + status);
                url = new URL(url, location);
            } catch (IOException error) {
                connection.disconnect();
                throw error;
            }
            connection.disconnect();
        }
        throw new IOException("Zbyt wiele przekierowań.");
    }

    private static String read(String url, int limit, AtomicBoolean cancelled) throws IOException {
        HttpURLConnection connection = connect(url);
        try (InputStream input = connection.getInputStream(); ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int n;
            while ((n = input.read(buffer)) != -1) {
                if (cancelled.get() || bytes.size() + n > limit) throw new IOException("Przerwano odczyt aktualizacji.");
                bytes.write(buffer, 0, n);
            }
            return new String(bytes.toByteArray(), StandardCharsets.UTF_8);
        } finally { connection.disconnect(); }
    }

    private interface Task { Runnable work(AtomicBoolean cancelled) throws Exception; }

    private static void run(Activity activity, String title, Task task) {
        AtomicBoolean cancelled = new AtomicBoolean();
        AlertDialog progress = new AlertDialog.Builder(activity).setTitle(title)
            .setNegativeButton("Anuluj", (dialog, which) -> cancelled.set(true))
            .setOnCancelListener(dialog -> cancelled.set(true)).show();
        Thread worker = new Thread(() -> {
            Runnable completion;
            try { completion = task.work(cancelled); }
            catch (Exception error) {
                completion = () -> message(activity, "Błąd aktualizacji",
                    error instanceof IOException ? error.getMessage() : "Nie udało się zweryfikować aktualizacji.");
            }
            Runnable result = completion;
            activity.runOnUiThread(() -> {
                if (activity.isFinishing() || activity.isDestroyed()) return;
                progress.dismiss();
                if (!cancelled.get()) result.run();
            });
        }, "PolishFighters-updates");
        worker.setDaemon(true);
        worker.start();
    }

    private static void message(Activity activity, String title, String details) {
        new AlertDialog.Builder(activity).setTitle(title).setMessage(details).setPositiveButton("OK", null).show();
    }
}
