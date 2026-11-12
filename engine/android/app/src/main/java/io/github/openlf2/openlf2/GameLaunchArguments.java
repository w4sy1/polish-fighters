package io.github.openlf2.openlf2;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONException;

/** Explicit paths let Android find every installed standalone package and the Lua hub. */
final class GameLaunchArguments {
    static String[] lan(File files, boolean host, String address, int port) throws IOException, JSONException {
        if (port < 1 || port > 65535) throw new IllegalArgumentException("Port: 1–65535.");
        if (!host) {
            String[] parts = address.split("\\.", -1);
            if (parts.length != 4) throw new IllegalArgumentException("Wpisz IPv4 gospodarza, np. 192.168.1.82.");
            for (String part : parts) {
                if (!part.matches("[0-9]{1,3}") || Integer.parseInt(part) > 255)
                    throw new IllegalArgumentException("Nieprawidłowy IPv4 gospodarza.");
            }
            if (address.startsWith("127.") || address.equals("0.0.0.0"))
                throw new IllegalArgumentException("Podaj adres drugiego urządzenia, nie localhost.");
        }
        List<String> args = new ArrayList<>(java.util.Arrays.asList(build(files, null, 0)));
        args.add("--room"); args.add(host ? "--host" : "--join"); args.add(host ? "0.0.0.0" : address);
        args.add("--port"); args.add(Integer.toString(port));
        return args.toArray(new String[0]);
    }
    static String[] build(File files, String role, int port) throws IOException, JSONException {
        File game = new File(files, "game");
        if (!new File(game, ".ready").isFile()) return new String[] {files.getAbsolutePath()};
        List<String> args = new ArrayList<>();
        args.add(game.getAbsolutePath());
        add(args, "--installer", new File(game, "LF2_v2.0a.exe"));
        add(args, "--scripts", new File(game, "scripts"));
        add(args, "--config-dir", new File(files, "settings"));
        GamePackSettings settings = new GamePackSettings(files);
        String mode = settings.mode();
        settings.save(mode, settings.selection(), settings.hideDuplicates());
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
