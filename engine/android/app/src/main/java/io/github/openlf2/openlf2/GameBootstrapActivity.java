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
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView status;
    private ProgressBar progress;
    private Button retry;

    @Override protected void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(48, 24, 48, 24);
        layout.setBackgroundColor(0xff101827);
        TextView title = new TextView(this);
        title.setText("POLISH FIGHTERS");
        title.setTextColor(0xffeeeeee);
        title.setTextSize(26);
        layout.addView(title);
        status = new TextView(this);
        status.setTextColor(0xffdddddd);
        status.setTextSize(17);
        status.setPadding(0, 24, 0, 24);
        layout.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        layout.addView(progress, new LinearLayout.LayoutParams(-1, -2));
        retry = new Button(this);
        retry.setText("SPRÓBUJ PONOWNIE");
        retry.setVisibility(android.view.View.GONE);
        retry.setOnClickListener(v -> begin());
        layout.addView(retry);
        setContentView(layout);
        begin();
    }

    private void begin() {
        retry.setVisibility(android.view.View.GONE);
        progress.setIndeterminate(true);
        status.setText("Przygotowywanie gry i modów…\nPierwsze uruchomienie może potrwać kilka minut.");
        worker.submit(() -> {
            try {
                prepare();
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
                    status.setText("Nie udało się przygotować gry.\n" + error.getMessage());
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

    private void prepare() throws IOException, JSONException, NoSuchAlgorithmException {
        final String version;
        try (InputStream id = getAssets().open("game-bundle.id")) {
            version = new String(readLimited(id, 128), StandardCharsets.US_ASCII).trim();
        } catch (FileNotFoundException absent) {
            return; // The original, unbundled build retains its normal download flow.
        }
        if (!version.matches("[0-9a-f]{64}")) throw new IOException("Nieprawidłowy identyfikator paczki.");
        File root = new File(getFilesDir(), "game");
        File marker = new File(root, ".ready");
        if (marker.isFile()) {
            try (InputStream old = new FileInputStream(marker)) {
                if (version.equals(new String(readLimited(old, 128), StandardCharsets.US_ASCII).trim())) return;
            }
        }
        File blobs = new File(root, ".blobs");
        if (!blobs.isDirectory() && !blobs.mkdirs()) throw new IOException("Nie można utworzyć katalogu gry.");
        try (ZipInputStream zip = new ZipInputStream(getAssets().open("game-bundle.zip"))) {
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
            long free = new StatFs(getFilesDir().getPath()).getAvailableBytes();
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
                if (unpacked % 50 == 0) showProgress(unpacked, sizes.size());
            }
            for (int n = 0; n < files.length(); n++) {
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
        }
    }

    private static void rename(File source, File target) throws IOException {
        try { Os.rename(source.getPath(), target.getPath()); }
        catch (ErrnoException error) { throw new IOException("Nie można zapisać " + target.getName(), error); }
    }

    private void showProgress(int current, int total) {
        runOnUiThread(() -> {
            if (isFinishing() || isDestroyed()) return;
            progress.setIndeterminate(false);
            progress.setMax(total);
            progress.setProgress(current);
            status.setText("Przygotowywanie gry i wszystkich modów: " + current + "/" + total
                    + "\nPliki wspólne są zapisywane tylko raz.");
        });
    }

    @Override protected void onDestroy() {
        worker.shutdownNow();
        super.onDestroy();
    }
}
