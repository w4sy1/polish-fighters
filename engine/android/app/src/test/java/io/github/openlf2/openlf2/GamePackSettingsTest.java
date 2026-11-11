package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import java.io.File;
import java.util.Arrays;
import java.util.List;
import org.json.JSONObject;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28, manifest = Config.NONE)
public class GamePackSettingsTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    private File readyGame() throws Exception {
        File game = temporary.newFolder("game");
        assertTrue(new File(game, ".ready").createNewFile());
        return game;
    }

    @Test public void defaultsToClassicAndHidesDuplicates() throws Exception {
        GamePackSettings settings = new GamePackSettings(temporary.getRoot());
        assertEquals("lf_two", settings.mode());
        assertTrue(settings.hideDuplicates());
    }

    @Test public void everySingleModuleLaunchesExactlyThatModule() throws Exception {
        File game = readyGame();
        GamePackSettings settings = new GamePackSettings(temporary.getRoot());
        for (int i = 0; i < GamePackSettings.IDS.length; i++) {
            settings.save(GamePackSettings.IDS[i], settings.selection(), true);
            List<String> args = Arrays.asList(GameLaunchArguments.build(temporary.getRoot(), null, 0));
            assertEquals(new File(game, "scripts").getAbsolutePath(), args.get(args.indexOf("--scripts") + 1));
            long mods = args.stream().filter("--mod"::equals).count();
            assertEquals(GamePackSettings.PACKS[i].isEmpty() ? 0 : 1, mods);
            if (mods != 0) assertEquals(new File(game, "content-packs/" + GamePackSettings.PACKS[i]).getAbsolutePath(),
                args.get(args.indexOf("--mod") + 1));
        }
    }

    @Test public void customSelectionSurvivesAndAllReenablesEveryPack() throws Exception {
        readyGame();
        GamePackSettings settings = new GamePackSettings(temporary.getRoot());
        boolean[] selected = new boolean[GamePackSettings.IDS.length];
        selected[0] = selected[3] = true;
        settings.save(GamePackSettings.CUSTOM, selected, true);
        assertArrayEquals(selected, new GamePackSettings(temporary.getRoot()).selection());
        List<String> args = Arrays.asList(GameLaunchArguments.build(temporary.getRoot(), null, 0));
        assertEquals(2, args.stream().filter("--mod"::equals).count());
        settings.save("lf_two", selected, true);
        assertArrayEquals(selected, settings.selection());
        settings.save(GamePackSettings.ALL, selected, true);
        for (boolean enabled : settings.selection()) assertTrue(enabled);
    }

    @Test public void emptyCustomSelectionCannotOverwriteExistingChoice() throws Exception {
        GamePackSettings settings = new GamePackSettings(temporary.getRoot());
        settings.save("polish_fighters", settings.selection(), false);
        try {
            settings.save(GamePackSettings.CUSTOM, new boolean[GamePackSettings.IDS.length], true);
            fail("An empty pool cannot start");
        } catch (IllegalArgumentException expected) { }
        assertEquals("polish_fighters", settings.mode());
        assertFalse(settings.hideDuplicates());
    }

    @Test public void packAndCodeSettingsPreserveEachOtherAndControls() throws Exception {
        MobileCodeSettings codes = new MobileCodeSettings(temporary.getRoot());
        codes.write(new JSONObject("{\"controls\":{\"keep\":true},\"progress\":7}"));
        codes.save(true);
        GamePackSettings packs = new GamePackSettings(temporary.getRoot());
        packs.save("dbz", packs.selection(), false);
        assertTrue(codes.enabled());
        codes.save(false, true);
        assertEquals("dbz", packs.mode());
        assertTrue(packs.hideDuplicates());
        assertTrue(codes.read().getJSONObject("controls").getBoolean("keep"));
        assertEquals(7, codes.read().getInt("progress"));
    }

    @Test public void bluetoothKeepsSelectedModuleAndAddsRoomTransportOnly() throws Exception {
        readyGame();
        GamePackSettings packs = new GamePackSettings(temporary.getRoot());
        packs.save("dbz", packs.selection(), true);
        for (String role : new String[] {"host", "join"}) {
            List<String> args = Arrays.asList(GameLaunchArguments.build(temporary.getRoot(), role, 32123));
            assertEquals(2, args.stream().filter("--mod"::equals).count());
            assertEquals("127.0.0.1", args.get(args.indexOf("--" + role) + 1));
            assertTrue(args.contains("32123"));
            assertFalse(args.stream().anyMatch(a -> a.endsWith("content-packs/mixed-all")));
        }
        assertFalse(Arrays.asList(GameLaunchArguments.build(temporary.getRoot(), "host", 0)).contains("--host"));
    }
}
