package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.content.Intent;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;

/**
 * Etap 1.14 / Zadanie 4A.3: OpenLF2Activity reads the one-shot
 * little_fighters_open_bluetooth settings flag the same way it already
 * reads little_fighters_open_android_tools (see takeAndroidToolsRequest /
 * the BluetoothLobbyActivity launch in onDestroy) and opens
 * BluetoothPairingActivity instead. main() itself calls into native code
 * (SDLActivity.nativeRunMain) and cannot run under Robolectric, so this
 * test drives the two pieces main() would otherwise wire together --
 * takeBluetoothRequest() clearing the settings flag, and onDestroy()
 * reading the resulting boolean field -- directly via reflection.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class OpenLF2ActivityBluetoothTest {
    @Test
    public void takeBluetoothRequestReadsAndClearsTheSettingsFlag() throws Exception {
        try (ActivityController<OpenLF2Activity> controller = Robolectric.buildActivity(OpenLF2Activity.class)) {
            OpenLF2Activity activity = controller.get();
            MobileCodeSettings settings = new MobileCodeSettings(activity.getFilesDir());
            org.json.JSONObject document = settings.read();
            document.put("little_fighters_open_bluetooth", true);
            settings.write(document);

            Method take = OpenLF2Activity.class.getDeclaredMethod("takeBluetoothRequest");
            take.setAccessible(true);
            assertTrue((Boolean) take.invoke(activity));
            assertFalse(settings.read().has("little_fighters_open_bluetooth"));
            assertFalse("a cleared flag must not be taken twice", (Boolean) take.invoke(activity));
        }
    }

    // onCreate() stages the Lua scripts from APK assets (copyAssetTree), which the unit-test
    // AssetManager does not provide -- so these two cases drive onDestroy() directly via
    // reflection instead of the full create()/destroy() lifecycle, same constraint that left
    // this Activity with no existing test coverage before this task (main() itself calls into
    // native code and cannot run under Robolectric either).
    @Test
    public void onDestroyOpensBluetoothPairingWhenRequested() throws Exception {
        OpenLF2Activity activity = Robolectric.buildActivity(OpenLF2Activity.class).get();
        Field flag = OpenLF2Activity.class.getDeclaredField("openBluetooth");
        flag.setAccessible(true);
        flag.setBoolean(activity, true);
        activity.finish();
        Method onDestroy = OpenLF2Activity.class.getDeclaredMethod("onDestroy");
        onDestroy.setAccessible(true);
        onDestroy.invoke(activity);
        Intent next = Shadows.shadowOf(activity).getNextStartedActivity();
        assertNotNull("onDestroy must launch BluetoothPairingActivity when openBluetooth is set", next);
        assertEquals(BluetoothPairingActivity.class.getName(), next.getComponent().getClassName());
    }

    @Test
    public void onDestroyDoesNotOpenBluetoothPairingWhenNotRequested() throws Exception {
        OpenLF2Activity activity = Robolectric.buildActivity(OpenLF2Activity.class).get();
        activity.finish();
        Method onDestroy = OpenLF2Activity.class.getDeclaredMethod("onDestroy");
        onDestroy.setAccessible(true);
        onDestroy.invoke(activity);
        Intent next = Shadows.shadowOf(activity).getNextStartedActivity();
        assertNull("no flag set, no follow-up activity must be started", next);
    }
}
