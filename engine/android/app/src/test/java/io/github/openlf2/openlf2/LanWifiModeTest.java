package io.github.openlf2.openlf2;
import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class LanWifiModeTest {
    @Test public void onlyLanAcquiresAndPauseReleases() {
        LanWifiMode mode = new LanWifiMode(RuntimeEnvironment.getApplication());
        mode.resume(false); assertFalse(mode.isHeld());
        mode.resume(true); assertTrue(mode.isHeld());
        mode.resume(true); assertTrue(mode.isHeld());
        mode.pause(); assertFalse(mode.isHeld());
        mode.pause(); assertFalse(mode.isHeld());
    }
    @Test @Config(sdk = 34) public void modernAndroidSupportsLowLatencyLifecycle() {
        LanWifiMode mode = new LanWifiMode(RuntimeEnvironment.getApplication());
        mode.resume(true); assertTrue(mode.isHeld());
        mode.pause(); assertFalse(mode.isHeld());
    }
}
