package io.github.openlf2.openlf2;

import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.Manifest;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import org.libsdl.app.SDLActivity;

/** Stages only the project's Lua modules before SDL starts the native entry point. */
public final class OpenLF2Activity extends SDLActivity {
    private static final String TAG = "OpenLF2";
    private LanWifiMode lanWifi;
    @Override protected void main() {
        GameDiagnostics.write(this, "launch-last.txt", "Native engine launch\n" + android.os.Build.VERSION.RELEASE);
        int result = SDLActivity.nativeRunMain(getMainSharedObject(), getMainFunction(), getArguments());
        if (result != 0) GameDiagnostics.write(this, "native-return.txt", "Native engine exit code: " + result);
    }

    /** Called on entering Bluetooth mode, never on application startup.
     * Native menu wiring is still required; callers recheck after the system dialog.
     */
    public boolean requestBluetoothPermissions() {
        final String[] needed;
        if (Build.VERSION.SDK_INT >= 31) {
            needed = new String[] {Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_ADVERTISE};
        } else if (Build.VERSION.SDK_INT >= 23) {
            needed = new String[] {Manifest.permission.ACCESS_FINE_LOCATION};
        } else {
            return true;
        }
        for (String permission : needed) {
            if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> requestPermissions(needed, 4201));
                return false;
            }
        }
        return true;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        GameDiagnostics.install(this);
        try {
            if (!new File(getFilesDir(), "game/.ready").isFile()) {
                copyAssetTree("scripts", new File(getFilesDir(), "scripts"));
            }
        } catch (IOException error) {
            Log.e(TAG, "Could not stage Lua modules", error);
            throw new IllegalStateException("Could not stage Lua modules", error);
        }
        super.onCreate(savedInstanceState);
        GitHubUpdates.attach(this);
    }

    @Override
    public void setOrientationBis(int width, int height, boolean resizable, String hint) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
    }

    /**
     * getFilesDir(), passed to native main() as its first argument. The native entry point
     * (src/adapters/sdl/entry.cpp) used to ask SDL for this same directory instead
     * (SDL_GetAndroidInternalStoragePath()), but that returned a pointer that was not safely
     * readable by the time native code ran; this Activity already has the same path reliably,
     * from staging the Lua modules above.
     */
    @Override
    protected String[] getArguments() {
        try {
            if (getIntent().hasExtra("lan_host")) {
                return GameLaunchArguments.lan(getFilesDir(), getIntent().getBooleanExtra("lan_host", false),
                    getIntent().getStringExtra("lan_address"), getIntent().getIntExtra("lan_port", 12345));
            }
            return GameLaunchArguments.build(getFilesDir(),
                getIntent().getStringExtra("bluetooth_role"),
                getIntent().getIntExtra("bluetooth_port", 0));
        } catch (IOException | org.json.JSONException error) {
            throw new IllegalStateException("Nie można odczytać wybranego modułu gry", error);
        }
    }

    @Override protected void onDestroy() {
        if (lanWifi != null) lanWifi.pause();
        BluetoothSession.closeCurrent();
        super.onDestroy();
    }
    @Override protected void onResume() {
        super.onResume();
        if (lanWifi == null) lanWifi = new LanWifiMode(this);
        lanWifi.resume(getIntent().hasExtra("lan_host"));
    }
    @Override protected void onPause() {
        if (lanWifi != null) lanWifi.pause();
        super.onPause();
    }

    private void copyAssetTree(String assetPath, File destination) throws IOException {
        String[] children = getAssets().list(assetPath);
        if (children == null) {
            throw new IOException("Cannot list " + assetPath);
        }
        if (children.length > 0) {
            if (!destination.isDirectory() && !destination.mkdirs()) {
                throw new IOException("Cannot create " + destination);
            }
            for (String child : children) {
                copyAssetTree(assetPath + "/" + child, new File(destination, child));
            }
            return;
        }
        try (InputStream source = getAssets().open(assetPath);
             OutputStream target = new FileOutputStream(destination)) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = source.read(buffer)) != -1) {
                target.write(buffer, 0, count);
            }
        }
    }
}
