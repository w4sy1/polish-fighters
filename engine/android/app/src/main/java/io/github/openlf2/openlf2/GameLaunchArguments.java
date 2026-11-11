package io.github.openlf2.openlf2;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONException;

/** Explicit paths let Android find every installed standalone package and the Lua hub. */
final class GameLaunchArguments {
    static String[] build(File files, String role, int port) throws IOException, JSONException {
        File game = new File(files, "game");
        if (!new File(game, ".ready").isFile()) return new String[] {files.getAbsolutePath()};
        List<String> args = new ArrayList<>();
        args.add(game.getAbsolutePath());
        add(args, "--installer", new File(game, "LF2_v2.0a.exe"));
        add(args, "--scripts", new File(game, "scripts"));
        add(args, "--config-dir", new File(files, "settings"));
        String mode = new GamePackSettings(files).mode();
        if (GamePackSettings.ALL.equals(mode) || GamePackSettings.CUSTOM.equals(mode)) {
            add(args, "--mod", new File(game, "content-packs/polish-originals"));
            add(args, "--mod", new File(game, "content-packs/mixed-all"));
        } else {
            for (int i = 0; i < GamePackSettings.IDS.length; i++) {
                if (GamePackSettings.IDS[i].equals(mode) && !GamePackSettings.PACKS[i].isEmpty()) {
                    add(args, "--mod", new File(game, "content-packs/" + GamePackSettings.PACKS[i]));
                }
            }
        }
        if (("host".equals(role) || "join".equals(role)) && port > 0 && port <= 65535) {
            args.add("--" + role); args.add("127.0.0.1");
            args.add("--port"); args.add(Integer.toString(port));
            add(args, "--mod", new File(game, "scripts/bluetooth-room"));
        }
        return args.toArray(new String[0]);
    }

    private static void add(List<String> args, String option, File path) {
        args.add(option); args.add(path.getAbsolutePath());
    }
}
