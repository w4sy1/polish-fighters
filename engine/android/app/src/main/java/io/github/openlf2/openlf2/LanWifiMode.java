package io.github.openlf2.openlf2;

import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.util.Log;

/** Low-latency Wi-Fi only while an explicitly launched LAN game is in the foreground. */
final class LanWifiMode {
    private final Context context;
    private WifiManager.WifiLock lock;
    LanWifiMode(Context context) { this.context = context.getApplicationContext(); }
    void resume(boolean lan) {
        if (!lan || isHeld()) return;
        WifiManager manager = (WifiManager)context.getSystemService(Context.WIFI_SERVICE);
        if (manager == null) return;
        try {
            int mode = Build.VERSION.SDK_INT >= 29 ? WifiManager.WIFI_MODE_FULL_LOW_LATENCY
                : WifiManager.WIFI_MODE_FULL_HIGH_PERF;
            lock = manager.createWifiLock(mode, "PolishFighters:LAN");
            lock.setReferenceCounted(false); lock.acquire();
            Log.i("OpenLF2", "LAN low-latency Wi-Fi active");
        } catch (SecurityException | UnsupportedOperationException error) {
            lock = null; Log.w("OpenLF2", "LAN Wi-Fi mode unavailable", error);
        }
    }
    void pause() {
        if (isHeld()) lock.release();
        lock = null;
    }
    boolean isHeld() { return lock != null && lock.isHeld(); }
}
