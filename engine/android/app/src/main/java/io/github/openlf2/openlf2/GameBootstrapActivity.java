package io.github.openlf2.openlf2;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.StatFs;
import android.system.ErrnoException;
import android.system.Os;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Unpacks the local game on a worker, with progress; SDL starts only when it is ready. */
public final class GameBootstrapActivity extends Activity {
    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView status;
    private ProgressBar progress;
    private Button retry;
    private TextView percent, loadingTitle, loadingNote;
    private Button updates;

    @Override protected void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        GameDiagnostics.install(this);
        setContentView(R.layout.activity_game_bootstrap);
        status = findViewById(R.id.pf_status);
        progress = findViewById(R.id.pf_progress);
        retry = findViewById(R.id.pf_retry);
        updates = findViewById(R.id.pf_updates);
        percent = findViewById(R.id.pf_loading_percent);
        loadingTitle = findViewById(R.id.pf_loading_title);
        loadingNote = findViewById(R.id.pf_loading_note);
        retry.setOnClickListener(v -> begin());
        updates.setOnClickListener(v -> {
            try { startActivity(new Intent(Intent.ACTION_VIEW, android.net.Uri.parse("https://github.com/w4sy1/polish-fighters/releases/latest"))); }
            catch (android.content.ActivityNotFoundException absent) { status.setText(R.string.pf_no_browser); }
        });
        begin();
    }

    private void begin() {
        retry.setVisibility(android.view.View.GONE);
        updates.setVisibility(android.view.View.GONE);
        loadingTitle.setText(R.string.pf_loading_title);
        loadingNote.setText(R.string.pf_loading_note);
        progress.setVisibility(android.view.View.VISIBLE);
        percent.setVisibility(android.view.View.VISIBLE);
        progress.setIndeterminate(true);
        percent.setText(getString(R.string.pf_percent, 0));
        status.setText(R.string.pf_loading_initial);
        worker.submit(() -> {
            long started = android.os.SystemClock.elapsedRealtime();
            try {
                prepare();
                android.util.Log.i("OpenLF2", "Startup prepare: " + (android.os.SystemClock.elapsedRealtime() - started) + " ms");
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    startActivity(new Intent(this, BluetoothLobbyActivity.class));
                    finish();
                });
            } catch (Exception error) {
                android.util.Log.e("OpenLF2", "Game preparation failed", error);
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    progress.setIndeterminate(false);
                    progress.setVisibility(android.view.View.GONE);
                    percent.setVisibility(android.view.View.GONE);
                    loadingTitle.setText(R.string.pf_error_title);
                    loadingNote.setText(R.string.pf_error_help);
                    status.setText(error.getMessage());
                    updates.setVisibility(android.view.View.VISIBLE);
                    retry.setVisibility(android.view.View.VISIBLE);
                });
            }
        });
    }

    private static byte[] readLimited(InputStream input, int limit) throws IOException {
        ByteArrayOutputStream result = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int n;
        while ((n = input.read(buffer)) != -1) {
            if (result.size() + n > limit) throw new IOException("Nieprawidłowy rozmiar indeksu gry.");
            result.write(buffer, 0, n);
        }
        return result.toByteArray();
    }

    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) result.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return result.toString();
    }

    interface BundleSource { InputStream open(String name) throws IOException; }
    interface BundleProgress { void update(boolean linking, int current, int total); }

    private void prepare() throws IOException, JSONException, NoSuchAlgorithmException {
        prepareBundle(name -> getAssets().open(name), getFilesDir(), this::showProgress);
    }

    static void prepareBundle(BundleSource bundleSource, File filesDirectory, BundleProgress report)
            throws IOException, JSONException, NoSuchAlgorithmException {
        final String version;
        try (InputStream id = bundleSource.open("game-bundle.id")) {
            version = new String(readLimited(id, 128), StandardCharsets.US_ASCII).trim();
        } catch (FileNotFoundException absent) {
            return; // The original, unbundled build retains its normal download flow.
        }
        if (!version.matches("[0-9a-f]{64}")) throw new IOException("Nieprawidłowy identyfikator paczki.");
        File root = new File(filesDirectory, "game");
        File marker = new File(root, ".ready");
        if (marker.isFile()) {
            try (InputStream old = new FileInputStream(marker)) {
                if (version.equals(new String(readLimited(old, 128), StandardCharsets.US_ASCII).trim())) return;
            }
        }
        File blobs = new File(root, ".blobs");
        if (!blobs.isDirectory() && !blobs.mkdirs()) throw new IOException("Nie można utworzyć katalogu gry.");
        // Inflate in Java from a buffered asset stream instead of crossing JNI for
        // every small inflater read (including skips of already installed blobs).
        try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(bundleSource.open("game-bundle.zip"), 256 * 1024))) {
            ZipEntry entry = zip.getNextEntry();
            if (entry == null || !entry.getName().equals("manifest.json")) throw new IOException("Brak indeksu paczki gry.");
            byte[] manifestBytes = readLimited(zip, 8 * 1024 * 1024);
            if (!hex(MessageDigest.getInstance("SHA-256").digest(manifestBytes)).equals(version)) throw new IOException("Uszkodzony indeks paczki gry.");
            JSONObject manifest = new JSONObject(new String(manifestBytes, StandardCharsets.UTF_8));
            if (manifest.getInt("schema") != 1) throw new IOException("Nieobsługiwana paczka gry.");
            JSONArray files = manifest.getJSONArray("files");
            if (files.length() > 30000) throw new IOException("Zbyt duża liczba plików gry.");
            Map<String, Long> sizes = new HashMap<>();
            String rootPrefix = root.getCanonicalPath() + File.separator;
            long missingBytes = 0;
            for (int n = 0; n < files.length(); n++) {
                JSONObject item = files.getJSONObject(n);
                String hash = item.getString("sha256");
                String name = item.getString("path");
                long size = item.getLong("bytes");
                if (!hash.matches("[0-9a-f]{64}") || size < 0 || size > 512L * 1024 * 1024
                        || name.startsWith("/") || name.contains("\\")
                        || !new File(root, name).getCanonicalPath().startsWith(rootPrefix)
                        || name.startsWith(".blobs/") || name.equals(".ready")) {
                    throw new IOException("Nieprawidłowa ścieżka lub rozmiar zasobu gry.");
                }
                if (!sizes.containsKey(hash)) {
                    sizes.put(hash, size);
                    File blob = new File(blobs, hash);
                    if (!blob.isFile() || blob.length() != size) missingBytes += size;
                }
            }
            long free = new StatFs(filesDirectory.getPath()).getAvailableBytes();
            if (free < missingBytes + 256L * 1024 * 1024) {
                throw new IOException("Za mało miejsca. Potrzeba jeszcze około "
                        + ((missingBytes + 256L * 1024 * 1024) / (1024 * 1024)) + " MB.");
            }
            int unpacked = 0;
            while ((entry = zip.getNextEntry()) != null) {
                if (Thread.currentThread().isInterrupted()) throw new IOException("Przygotowanie przerwane.");
                String name = entry.getName();
                if (!name.matches("blobs/[0-9a-f]{64}")) throw new IOException("Nieprawidłowy plik paczki.");
                String hash = name.substring(6);
                Long size = sizes.get(hash);
                if (size == null) throw new IOException("Zasób spoza indeksu paczki.");
                File target = new File(blobs, hash);
                if (!target.isFile() || target.length() != size) {
                    File partial = new File(blobs, hash + ".part");
                    MessageDigest digest = MessageDigest.getInstance("SHA-256");
                    long count = 0;
                    try (FileOutputStream output = new FileOutputStream(partial)) {
                        byte[] buffer = new byte[65536];
                        int n;
                        while ((n = zip.read(buffer)) != -1) {
                            if (Thread.currentThread().isInterrupted()) throw new IOException("Przygotowanie przerwane.");
                            count += n;
                            if (count > size) throw new IOException("Nieprawidłowy rozmiar zasobu.");
                            output.write(buffer, 0, n);
                            digest.update(buffer, 0, n);
                        }
                    }
                    if (count != size || !hex(digest.digest()).equals(hash)) throw new IOException("Uszkodzony zasób gry.");
                    rename(partial, target);
                }
                unpacked++;
                if (unpacked % 50 == 0) report.update(false, unpacked, sizes.size());
            }
            for (int n = 0; n < files.length(); n++) {
                if (Thread.currentThread().isInterrupted()) throw new IOException("Przygotowanie przerwane.");
                if (n % 50 == 0) report.update(true, n, files.length());
                JSONObject item = files.getJSONObject(n);
                File blob = new File(blobs, item.getString("sha256"));
                if (!blob.isFile() || blob.length() != item.getLong("bytes")) throw new IOException("Niekompletna paczka gry.");
                File target = new File(root, item.getString("path"));
                File parent = target.getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Nie można zapisać plików gry.");
                File temporary = new File(target.getPath() + ".part");
                if (temporary.exists() && !temporary.delete()) throw new IOException("Nie można wznowić przygotowania.");
                try {
                    Os.link(blob.getPath(), temporary.getPath());
                } catch (ErrnoException noHardlinks) {
                    try (InputStream source = new FileInputStream(blob);
                         FileOutputStream output = new FileOutputStream(temporary)) {
                        byte[] buffer = new byte[65536];
                        int count;
                        while ((count = source.read(buffer)) != -1) output.write(buffer, 0, count);
                    }
                }
                rename(temporary, target);
            }
            File ready = new File(root, ".ready.part");
            try (FileOutputStream output = new FileOutputStream(ready)) {
                output.write(version.getBytes(StandardCharsets.US_ASCII));
            }
            rename(ready, marker);
            report.update(true, files.length(), files.length());
        }
    }

    private static void rename(File source, File target) throws IOException {
        try { Os.rename(source.getPath(), target.getPath()); }
        catch (ErrnoException error) { throw new IOException("Nie można zapisać " + target.getName(), error); }
    }

    private void showProgress(boolean linking, int current, int total) {
        runOnUiThread(() -> {
            if (isFinishing() || isDestroyed()) return;
            int value = total == 0 ? 100 : (int)((long)current * 100 / total);
            int completed = linking ? 85 + value * 15 / 100 : value * 85 / 100;
            progress.setIndeterminate(false);
            progress.setMax(100);
            progress.setProgress(completed);
            percent.setText(getString(R.string.pf_percent, completed));
            status.setText(getString(linking ? R.string.pf_progress_link : R.string.pf_progress_unpack, current, total));
        });
    }

    @Override protected void onDestroy() {
        worker.shutdownNow();
        super.onDestroy();
    }
}
