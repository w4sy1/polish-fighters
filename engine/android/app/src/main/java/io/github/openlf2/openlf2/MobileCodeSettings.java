package io.github.openlf2.openlf2;

import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.json.JSONException;
import org.json.JSONObject;

/** Edits the engine's existing option before SDL starts, preserving other settings. */
final class MobileCodeSettings {
    private final File directory;
    private final AtomicFile file;

    MobileCodeSettings(File filesDirectory) {
        directory = new File(filesDirectory, "settings");
        file = new AtomicFile(new File(directory, "config.json"));
    }

    JSONObject read() throws IOException, JSONException {
        if (!file.getBaseFile().exists()
                && !new File(file.getBaseFile().getPath() + ".bak").exists()) return new JSONObject();
        return new JSONObject(new String(file.readFully(), StandardCharsets.UTF_8));
    }

    boolean enabled() throws IOException, JSONException {
        JSONObject options = read().optJSONObject("options");
        return options != null && options.optBoolean("unlock_characters", false);
    }

    void save(boolean enabled) throws IOException, JSONException {
        save(enabled, null);
    }

    void save(boolean enabled, Boolean hideDuplicates) throws IOException, JSONException {
        save(enabled, hideDuplicates, null);
    }

    String touchLayout() throws IOException, JSONException {
        JSONObject options = read().optJSONObject("options");
        if (options == null) return "classic";
        return options.optString("touch_layout", options.optBoolean("digipad", true) ? "classic" : "modern");
    }

    void save(boolean enabled, Boolean hideDuplicates, String touchLayout) throws IOException, JSONException {
        if (touchLayout != null && !touchLayout.equals("classic") && !touchLayout.equals("modern"))
            throw new IllegalArgumentException("Nieprawidłowy układ dotykowy");
        JSONObject document = read();
        JSONObject options = document.optJSONObject("options");
        if (options == null) {
            if (document.has("options")) throw new JSONException("Nieprawidłowe ustawienia gry");
            options = new JSONObject();
        }
        options.put("unlock_characters", enabled);
        if (touchLayout != null) {
            options.put("touch_layout", touchLayout);
            options.put("digipad", touchLayout.equals("classic"));
        }
        document.put("options", options);
        if (hideDuplicates != null) document.put("little_fighters_hide_duplicates", hideDuplicates);
        if (!document.has("version")) document.put("version", 1);
        write(document);
    }

    void write(JSONObject document) throws IOException {
        if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("Nie można utworzyć ustawień");
        FileOutputStream output = file.startWrite();
        try {
            output.write(document.toString().getBytes(StandardCharsets.UTF_8));
            file.finishWrite(output);
        } catch (IOException error) {
            file.failWrite(output);
            throw error;
        }
    }
}
