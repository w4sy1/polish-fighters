package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.JSONObject;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.rules.TemporaryFolder;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28, manifest = Config.NONE)
public class MobileCodeSettingsTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    @Test public void freshInstallCanEnableAndDisableCodes() throws Exception {
        MobileCodeSettings settings = new MobileCodeSettings(temporary.getRoot());
        assertFalse(settings.enabled());
        settings.save(true);
        assertTrue(new MobileCodeSettings(temporary.getRoot()).enabled());
        settings.save(false);
        assertFalse(new MobileCodeSettings(temporary.getRoot()).enabled());
    }

    @Test public void changingCodesPreservesControlsProgressAndOtherOptions() throws Exception {
        File directory = temporary.newFolder("settings");
        File config = new File(directory, "config.json");
        String original = "{\"options\":{\"language\":\"polish\",\"show_gamepad\":true},"
            + "\"controls\":[1,2,3],\"polish_fighters_progress\":{\"wins\":7}}";
        Files.write(config.toPath(), original.getBytes(StandardCharsets.UTF_8));
        MobileCodeSettings settings = new MobileCodeSettings(temporary.getRoot());
        settings.save(true);
        JSONObject saved = new JSONObject(new String(Files.readAllBytes(config.toPath()), StandardCharsets.UTF_8));
        assertEquals("polish", saved.getJSONObject("options").getString("language"));
        assertTrue(saved.getJSONObject("options").getBoolean("show_gamepad"));
        assertEquals("[1,2,3]", saved.getJSONArray("controls").toString());
        assertEquals(7, saved.getJSONObject("polish_fighters_progress").getInt("wins"));
        assertTrue(saved.getJSONObject("options").getBoolean("unlock_characters"));
    }

    @Test public void malformedConfigIsNotOverwritten() throws Exception {
        File config = new File(temporary.newFolder("settings"), "config.json");
        Files.write(config.toPath(), "broken JSON".getBytes(StandardCharsets.UTF_8));
        try {
            new MobileCodeSettings(temporary.getRoot()).save(true);
            fail("Corrupt settings must be reported");
        } catch (org.json.JSONException expected) { }
        assertEquals("broken JSON", new String(Files.readAllBytes(config.toPath()), StandardCharsets.UTF_8));
    }

    @Test public void interruptedAtomicWriteRetainsSavedChoice() throws Exception {
        MobileCodeSettings settings = new MobileCodeSettings(temporary.getRoot());
        settings.save(true);
        AtomicFile atomic = new AtomicFile(new File(temporary.getRoot(), "settings/config.json"));
        FileOutputStream partial = atomic.startWrite();
        partial.write("{broken".getBytes(StandardCharsets.UTF_8));
        atomic.failWrite(partial);
        assertTrue(new MobileCodeSettings(temporary.getRoot()).enabled());
    }
}
