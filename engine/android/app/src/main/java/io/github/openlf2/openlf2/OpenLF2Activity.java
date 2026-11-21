package io.github.openlf2.openlf2;

import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.Manifest;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import org.libsdl.app.SDLActivity;

/** Stages only the project's Lua modules before SDL starts the native entry point. */
public final class OpenLF2Activity extends SDLActivity {
    private static final String TAG = "OpenLF2";
    private static final String OPEN_ANDROID_TOOLS = "little_fighters_open_android_tools";
    private LanWifiMode lanWifi;
    private File stagedScripts;
    private volatile boolean openAndroidTools;
    @Override protected void main() {
        GameDiagnostics.write(this, "launch-last.txt", "Native engine launch\n" + android.os.Build.VERSION.RELEASE);
        takeAndroidToolsRequest(); // Discard requests left behind by an interrupted game.
        int result = SDLActivity.nativeRunMain(getMainSharedObject(), getMainFunction(), getArguments());
        openAndroidTools = result == 0 && takeAndroidToolsRequest();
        if (result != 0) GameDiagnostics.write(this, "native-return.txt", "Native engine exit code: " + result);
    }

    /** Called by the SDL main thread while the game's menu is active. */
    public void showModManager() {
        runOnUiThread(() -> {
            if (!isFinishing() && !isDestroyed()) {
                startActivity(new Intent(this, AndroidModsActivity.class)
                    .putExtra(AndroidModsActivity.FROM_RUNNING_GAME, true));
            }
        });
    }

    /** Called by the in-game Information menu. */
    public void checkGameUpdate() {
        runOnUiThread(() -> {
            if (!isFinishing() && !isDestroyed()) GitHubUpdates.check(this);
        });
    }

    private boolean takeAndroidToolsRequest() { return takeRequest(OPEN_ANDROID_TOOLS); }

    private boolean takeRequest(String key) {
        try {
            MobileCodeSettings settings = new MobileCodeSettings(getFilesDir());
            org.json.JSONObject document = settings.read();
            if (!document.optBoolean(key)) return false;
            document.remove(key);
            settings.write(document);
            return true;
        } catch (IOException | org.json.JSONException error) {
            Log.w(TAG, "Could not read or clear the Android tools request", error);
            return false;
        }
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
            if (!usesCurrentBundle()) {
                stagedScripts = new File(getFilesDir(), "scripts");
                copyAssetTree("scripts", stagedScripts);
            }
        } catch (IOException error) {
            Log.e(TAG, "Could not stage Lua modules", error);
            throw new IllegalStateException("Could not stage Lua modules", error);
        }
        super.onCreate(savedInstanceState);
    }

    private boolean usesCurrentBundle() throws IOException {
        if (!new File(getFilesDir(), "game/.ready").isFile()) return false;
        try (InputStream id = getAssets().open("game-bundle.id")) {
            return true;
        } catch (FileNotFoundException absent) {
            // A small APK can update a previous full install. Use its own Lua
            // files and keep the already unpacked game data and modules.
            return false;
        }
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
            String[] launch = getIntent().hasExtra("lan_host")
                ? GameLaunchArguments.lan(getFilesDir(), getIntent().getBooleanExtra("lan_host", false),
                    getIntent().getStringExtra("lan_address"), getIntent().getIntExtra("lan_port", 12345), stagedScripts)
                : GameLaunchArguments.build(getFilesDir(), getIntent().getStringExtra("bluetooth_role"),
                    getIntent().getIntExtra("bluetooth_port", 0), stagedScripts);
            String[] withVersion = java.util.Arrays.copyOf(launch, launch.length + 2);
            withVersion[launch.length] = "--android-version";
            withVersion[launch.length + 1] = BuildConfig.VERSION_NAME;
            return withVersion;
        } catch (IOException | org.json.JSONException error) {
            throw new IllegalStateException("Nie można odczytać wybranego modułu gry", error);
        }
    }

    @Override protected void onDestroy() {
        if (lanWifi != null) lanWifi.pause();
        BluetoothSession.closeCurrent();
        super.onDestroy();
        if (isFinishing() && openAndroidTools) {
            startActivity(new Intent(this, BluetoothLobbyActivity.class));
        }
    }
    /**
     * The Back key is the game's Esc. When no SDL view holds focus (for example right after
     * the account screen stops text input) Android used to finish the activity instead,
     * which closed the whole game. The soft keyboard still consumes Back before this point.
     */
    @Override public boolean dispatchKeyEvent(android.view.KeyEvent event) {
        if (event.getKeyCode() == android.view.KeyEvent.KEYCODE_BACK
            && (event.getSource() & android.view.InputDevice.SOURCE_MOUSE) != android.view.InputDevice.SOURCE_MOUSE) {
            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                SDLActivity.onNativeKeyDown(android.view.KeyEvent.KEYCODE_BACK);
            } else if (event.getAction() == android.view.KeyEvent.ACTION_UP) {
                SDLActivity.onNativeKeyUp(android.view.KeyEvent.KEYCODE_BACK);
            }
            return true;
        }
        return super.dispatchKeyEvent(event);
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
