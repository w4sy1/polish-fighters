package io.github.openlf2.openlf2;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;

/**
 * Etap 1.14 / Etap 4A: dedicated Bluetooth pairing screen with exactly four
 * actions (search/host/join/back), reusing BluetoothSession's RFCOMM logic
 * unchanged. Replaces the room/tcp/lan/bluetooth rows that used to live
 * inside the Android tools screen's "network" dialog
 * (BluetoothLobbyActivity.showConnections) -- that screen keeps serving
 * little_fighters_open_android_tools unchanged (module picker, settings,
 * diagnostics; see StartScreenTest), this is a separate, narrower screen
 * reachable only through the new GRAJ ZDALNIE -> BLUETOOTH row.
 */
public final class BluetoothPairingActivity extends Activity {
    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }
    private TextView status;
    private final List<Button> actions = new ArrayList<>();
    private BluetoothSession session;
    private boolean transferred;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_game_home);
        status = findViewById(R.id.pf_status);
        Button search = findViewById(R.id.pf_module);
        Button host = findViewById(R.id.pf_network);
        Button join = findViewById(R.id.pf_settings);
        Button back = findViewById(R.id.pf_quit);
        java.util.Collections.addAll(actions, search, host, join, back);
        search.setText("SZUKAJ URZĄDZEŃ");
        host.setText("UTWÓRZ POKÓJ");
        join.setText("DOŁĄCZ");
        back.setText("WSTECZ");
        search.setOnClickListener(v -> pair());
        host.setOnClickListener(v -> connect(true));
        join.setOnClickListener(v -> connect(false));
        back.setOnClickListener(v -> leave());
        Button cancel = findViewById(R.id.pf_cancel);
        cancel.setOnClickListener(v -> {
            BluetoothSession.closeCurrent(); session = null;
            for (Button action : actions) action.setEnabled(true);
            cancel.setVisibility(android.view.View.GONE);
            status.setText(R.string.pf_ready);
        });
    }
    @Override protected void onResume() {
        super.onResume();
        if (adapter() == null) status.setText("Ten telefon nie udostępnia Bluetooth. Wybierz grę lokalną.");
    }
    private BluetoothAdapter adapter() { return BluetoothAdapter.getDefaultAdapter(); }
    private void pair() {
        try { startActivity(new Intent(android.provider.Settings.ACTION_BLUETOOTH_SETTINGS)); }
        catch (android.content.ActivityNotFoundException absent) {
            status.setText("Otwórz ustawienia Bluetooth telefonu i sparuj oba telefony.");
        }
    }
    @SuppressLint("MissingPermission") // Explicit runtime gate below; no discovery or location access.
    private void connect(boolean host) {
        if (Build.VERSION.SDK_INT >= 31 && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT}, 4202);
            status.setText("Zezwól na połączenie z urządzeniami w pobliżu, a następnie wybierz tryb ponownie.");
            return;
        }
        BluetoothAdapter adapter = adapter();
        if (adapter == null) { status.setText("Ten telefon nie udostępnia Bluetooth. Wybierz grę lokalną."); return; }
        try {
            if (!adapter.isEnabled()) {
                startActivityForResult(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 4203);
                status.setText("Włącz Bluetooth i ponownie wybierz tryb."); return;
            }
            if (host) { start(adapter, null); return; }
            List<BluetoothDevice> peers = new ArrayList<>(adapter.getBondedDevices());
            if (peers.isEmpty()) { status.setText("Brak sparowanych urządzeń. Sparuj oba telefony przez SZUKAJ URZĄDZEŃ."); return; }
            String[] labels = new String[peers.size()];
            for (int i = 0; i < peers.size(); i++) {
                BluetoothDevice device = peers.get(i);
                labels[i] = (device.getName() == null ? "Telefon" : device.getName()) + "\n" + device.getAddress();
            }
            new AlertDialog.Builder(this).setTitle("Wybierz telefon, który założył grę")
                .setItems(labels, (dialog, index) -> start(adapter, peers.get(index)))
                .setNegativeButton("Anuluj", null).show();
        } catch (SecurityException error) {
            status.setText("Brak zgody na Bluetooth. Sprawdź uprawnienia aplikacji w ustawieniach Androida.");
        }
    }
    private void start(BluetoothAdapter adapter, BluetoothDevice peer) {
        findViewById(R.id.pf_cancel).setVisibility(android.view.View.VISIBLE);
        for (Button action : actions) action.setEnabled(false);
        status.setText(peer == null ? "Czekam na drugi telefon. Na nim wybierz DOŁĄCZ."
            : "Łączenie z drugim telefonem…");
        session = BluetoothSession.create();
        final BluetoothSession attempt = session;
        session.start(adapter, peer, new BluetoothSession.Listener() {
            public void ready(String role, int port) { runOnUiThread(() -> {
                if (!isFinishing() && !isDestroyed() && session == attempt) launch(role, port);
            }); }
            public void failed(String message) { runOnUiThread(() -> {
                if (session != attempt) return;
                if (transferred) {
                    Toast.makeText(getApplicationContext(), message, Toast.LENGTH_LONG).show();
                } else if (!isFinishing() && !isDestroyed()) {
                    status.setText(message + "\nMożesz ponowić połączenie.");
                    for (Button action : actions) action.setEnabled(true);
                }
            }); }
        });
    }
    private void launch(String role, int port) {
        Intent game = new Intent(this, OpenLF2Activity.class);
        game.putExtra("bluetooth_role", role); game.putExtra("bluetooth_port", port);
        transferred = true; startActivity(game); finish();
    }
    // Always returns to the real menu with little_fighters_start_menu='remote' saved, so the
    // Lua hub reopens directly on GRAJ ZDALNIE instead of its root (unlike the old
    // BluetoothLobbyActivity.launch(null,0), which left no flag and no RFCOMM link to tear down).
    private void leave() {
        if (session != null) { BluetoothSession.closeCurrent(); session = null; }
        try {
            MobileCodeSettings settings = new MobileCodeSettings(getFilesDir());
            JSONObject document = settings.read();
            document.put("little_fighters_start_menu", "remote");
            settings.write(document);
        } catch (java.io.IOException | org.json.JSONException error) {
            // Best effort: if the settings write fails the player still gets back to the
            // real menu, just not pre-opened on GRAJ ZDALNIE.
        }
        transferred = true;
        startActivity(new Intent(this, OpenLF2Activity.class));
        finish();
    }
    @Override public void onBackPressed() { leave(); }
    @Override protected void onDestroy() {
        if (!transferred && session != null) session.close();
        super.onDestroy();
    }
}
