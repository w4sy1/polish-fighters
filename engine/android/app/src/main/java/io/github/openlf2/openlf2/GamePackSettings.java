package io.github.openlf2.openlf2;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Uses the same package selection as the desktop Lua launcher (hub.lua hub.profiles). Keep
 * these three arrays and hub.profiles in sync by id/title/directory - this is a separate,
 * hand-maintained copy, not read from the Lua table. 2026-11-23: dragon_ball_super,
 * ntsd_community, mortal_kombat, lf3 and oplos were released in mods/catalog.json and
 * downloaded fine (AndroidModsActivity.install), but were missing from IDS/PACKS here, so
 * save() below rejected them with "Nieznany moduł" the moment the player tapped WYBIERZ -
 * the pack looked installed but could never actually be selected.
 */
final class GamePackSettings {
    static final String[] IDS = {"polish_fighters", "lf_two", "lf_four_turbo", "dbz",
        "one_piece", "kate", "reinforced", "ntsd", "bleach",
        "dragon_ball_super", "ntsd_community", "mortal_kombat", "lf3", "oplos"};
    static final String[] TITLES = {"Polish Fighters", "Little Fighter 2", "LF4 Turbo",
        "Dragon Ball", "One Piece", "Kate", "Reinforced", "NTSD / Naruto", "Bleach",
        "Dragon Ball Super", "NTSD Community", "Mortal Kombat LF2", "LF3BYTITASZIBIKAS 2.0b",
        "One Piece: Legends of Sea"};
    static final String[] PACKS = {"polish-originals", "", "lf4-turbo", "dbz",
        "one-piece", "kate", "reinforced", "ntsd", "bleach",
        "dragon-ball-super", "ntsd-community", "mortal-kombat", "lf3", "oplos"};
    static final String ALL = "all", CUSTOM = "custom";
    private final MobileCodeSettings store;
    private final File filesDirectory;

    GamePackSettings(File filesDirectory) { this.filesDirectory = filesDirectory; store = new MobileCodeSettings(filesDirectory); }

    boolean needsFirstSetup() {
        try {
            return !store.read().has("little_fighters_start_profile");
        } catch (IOException | JSONException error) {
            android.util.Log.w("OpenLF2", "Could not read game profile", error);
            return false;
        }
    }

    boolean hasPack(String id) {
        return new File(filesDirectory, "game/content-packs/" + id + "/package.manifest").isFile();
    }

    String mode() throws IOException, JSONException {
        String mode = store.read().optString("little_fighters_start_profile", "lf_two");
        if (ALL.equals(mode) || CUSTOM.equals(mode)) return mode;
        for (String id : IDS) if (id.equals(mode)) return mode;
        if (isImported(mode) || isOptionalInstalled(mode)) return mode;
        return "lf_two";
    }

    // dragon_ball_super and ntsd_community moved into IDS above (2026-11-23); left out of this
    // switch now that they are first-class entries, not "additional" ones.
    static String optionalTitle(String id) {
        switch (id) {
            case "fighter_hero": return "Fighter Hero";
            case "gf2": return "GF2";
            case "lf2_ns": return "LF2 NS";
            case "sx2": return "Sx2";
            case "lf2_sv": return "LF2 SV";
            case "rn_lf2": return "RN LF2";
            case "lf_seed": return "LF Seed";
            case "wlf2_al": return "WLF2 AL";
            case "ce_lf2": return "CE LF2";
            case "ntsd_ce_setup": return "NTSD CE";
            case "killer_lf2": return "Killer LF2";
            default: return null;
        }
    }

    private boolean isOptionalInstalled(String id) {
        return optionalTitle(id) != null && hasPack(id.replace('_', '-'));
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
        if (isOptionalInstalled(mode)) return optionalTitle(mode);
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

    /**
     * IDs the user asked the first-run screen to fetch in one batch (point 4: multi-select
     * download). Persisted before the queue starts, so killing the app or losing the network
     * mid-batch and reopening setup resumes with already-installed IDs skipped, not re-asked.
     */
    java.util.LinkedHashSet<String> prefetchQueue() throws IOException, JSONException {
        JSONObject saved = store.read().optJSONObject("little_fighters_prefetch");
        java.util.LinkedHashSet<String> result = new java.util.LinkedHashSet<>();
        if (saved != null) {
            JSONArray keys = saved.names();
            for (int i = 0; keys != null && i < keys.length(); i++) {
                String id = keys.optString(i, null);
                if (id != null && saved.optBoolean(id, false)) result.add(id);
            }
        }
        return result;
    }

    void savePrefetchQueue(java.util.Set<String> ids) throws IOException, JSONException {
        JSONObject document = store.read();
        JSONObject packed = new JSONObject();
        for (String id : ids) packed.put(id, true);
        document.put("little_fighters_prefetch", packed);
        if (!document.has("version")) document.put("version", 1);
        store.write(document);
    }

    void save(String mode, boolean[] selected, boolean hideDuplicates) throws IOException, JSONException {
        boolean valid = ALL.equals(mode) || CUSTOM.equals(mode);
        for (String id : IDS) valid |= id.equals(mode);
        valid |= isImported(mode) || isOptionalInstalled(mode);
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
