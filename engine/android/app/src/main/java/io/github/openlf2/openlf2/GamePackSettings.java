package io.github.openlf2.openlf2;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONException;
import org.json.JSONObject;

/** Uses the same package selection as the desktop Lua launcher. */
final class GamePackSettings {
    static final String[] IDS = {"polish_fighters", "lf_two", "lf_four_turbo", "dbz",
        "one_piece", "kate", "reinforced", "ntsd", "bleach"};
    static final String[] TITLES = {"Polish Fighters", "Little Fighter 2", "LF4 Turbo",
        "Dragon Ball", "One Piece", "Kate", "Reinforced", "NTSD / Naruto", "Bleach"};
    static final String[] PACKS = {"polish-originals", "", "lf4-turbo", "dbz",
        "one-piece", "kate", "reinforced", "ntsd", "bleach"};
    static final String ALL = "all", CUSTOM = "custom";
    private final MobileCodeSettings store;
    private final File filesDirectory;

    GamePackSettings(File filesDirectory) { this.filesDirectory = filesDirectory; store = new MobileCodeSettings(filesDirectory); }

    String mode() throws IOException, JSONException {
        String mode = store.read().optString("little_fighters_start_profile", "lf_two");
        if (ALL.equals(mode) || CUSTOM.equals(mode)) return mode;
        for (String id : IDS) if (id.equals(mode)) return mode;
        if (isImported(mode)) return mode;
        return "lf_two";
    }

    private boolean isImported(String id) {
        return id != null && id.matches("mod-[a-f0-9]{24}")
            && new File(new File(filesDirectory, "game/content-packs"), id + "/package.manifest").isFile();
    }

    List<String> imported() {
        File root = new File(filesDirectory, "game/content-packs");
        File[] children = root.listFiles(File::isDirectory);
        List<String> result = new ArrayList<>();
        if (children != null) for (File child : children) if (isImported(child.getName())) result.add(child.getName());
        java.util.Collections.sort(result);
        return result;
    }

    String label() throws IOException, JSONException {
        String mode = mode();
        if (ALL.equals(mode)) return "Wszystkie razem";
        if (CUSTOM.equals(mode)) return "Własny zestaw modułów";
        for (int i = 0; i < IDS.length; i++) if (IDS[i].equals(mode)) return TITLES[i];
        if (isImported(mode)) return "MOD " + mode.substring(4, 12);
        throw new IllegalStateException("Unknown game profile");
    }

    boolean[] selection() throws IOException, JSONException {
        JSONObject selected = store.read().optJSONObject("little_fighters_packs");
        boolean[] result = new boolean[IDS.length];
        for (int i = 0; i < result.length; i++) result[i] = selected == null || selected.optBoolean(IDS[i], true);
        return result;
    }

    boolean hideDuplicates() throws IOException, JSONException {
        return store.read().optBoolean("little_fighters_hide_duplicates", true);
    }

    void save(String mode, boolean[] selected, boolean hideDuplicates) throws IOException, JSONException {
        boolean valid = ALL.equals(mode) || CUSTOM.equals(mode);
        for (String id : IDS) valid |= id.equals(mode);
        valid |= isImported(mode);
        if (!valid) throw new IllegalArgumentException("Nieznany moduł");
        if (selected == null || selected.length != IDS.length) throw new IllegalArgumentException("Nieprawidłowa lista modułów");
        int count = 0;
        JSONObject packs = new JSONObject();
        for (int i = 0; i < IDS.length; i++) {
            boolean enabled = ALL.equals(mode) || selected[i];
            if (enabled) count++;
            packs.put(IDS[i], enabled);
        }
        if (count == 0 && CUSTOM.equals(mode)) throw new IllegalArgumentException("Wybierz przynajmniej jeden moduł");
        JSONObject document = store.read();
        document.put("little_fighters_start_profile", mode);
        document.put("little_fighters_packs", packs);
        document.put("little_fighters_hide_duplicates", hideDuplicates);
        if (!document.has("version")) document.put("version", 1);
        store.write(document);
    }
}
