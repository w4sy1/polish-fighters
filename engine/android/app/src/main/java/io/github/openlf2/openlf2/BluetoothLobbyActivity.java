package io.github.openlf2.openlf2;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;

/** Offline play and paired-device Bluetooth entry, before native SDL starts. */
public final class BluetoothLobbyActivity extends Activity {
    private TextView status;
    private final List<Button> actions = new ArrayList<>();
    private BluetoothSession session;
    private boolean transferred;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL); layout.setPadding(32, 12, 32, 12);
        layout.setBackgroundColor(0xff101827);
        status = new TextView(this); status.setTextColor(0xffeeeeee); status.setTextSize(17);
        status.setText("POLISH FIGHTERS\nBluetooth: wersja próbna dla dwóch telefonów. Najpierw sparuj je w ustawieniach Androida. Na obu zainstaluj ten sam APK.");
        layout.addView(status);
        button(layout, "GRAJ NA TYM TELEFONIE", () -> launch(null, 0));
        button(layout, "USTAWIENIA", this::showSettings);
        button(layout, "BLUETOOTH: ZAŁÓŻ GRĘ", () -> connect(true));
        button(layout, "BLUETOOTH: DOŁĄCZ", () -> connect(false));
        button(layout, "PAROWANIE / USTAWIENIA BLUETOOTH", () -> {
            try { startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)); }
            catch (android.content.ActivityNotFoundException absent) { status.setText("Otwórz ustawienia Bluetooth telefonu i sparuj oba telefony."); }
        });
        Button cancel = new Button(this); cancel.setText("ANULUJ POŁĄCZENIE");
        cancel.setOnClickListener(v -> {
            BluetoothSession.closeCurrent(); session = null;
            for (Button action : actions) action.setEnabled(true);
            status.setText("Anulowano. Możesz zagrać lokalnie albo ponowić Bluetooth.");
        });
        layout.addView(cancel);
        ScrollView scroll = new ScrollView(this); scroll.addView(layout); setContentView(scroll);
    }
    private void button(LinearLayout layout, String label, Runnable action) {
        Button button = new Button(this); button.setText(label);
        button.setOnClickListener(v -> action.run()); actions.add(button); layout.addView(button);
    }
    private void showSettings() {
        final MobileCodeSettings settings = new MobileCodeSettings(getFilesDir());
        final CheckBox codes = new CheckBox(this);
        codes.setText("Włącz kody — odblokuj ukryte postacie");
        codes.setPadding(32, 24, 32, 24);
        try { codes.setChecked(settings.enabled()); }
        catch (java.io.IOException | org.json.JSONException error) {
            new AlertDialog.Builder(this).setTitle("Błąd ustawień")
                .setMessage("Nie można odczytać ustawień: " + error.getMessage())
                .setPositiveButton("OK", null).show();
            return;
        }
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Ustawienia")
            .setView(codes).setPositiveButton("Zapisz", null)
            .setNegativeButton("Anuluj", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(view -> {
                try {
                    boolean wasEnabled = settings.enabled();
                    settings.save(codes.isChecked());
                    dialog.dismiss();
                    if (codes.isChecked() && !wasEnabled) {
                        new AlertDialog.Builder(this).setTitle("lamus")
                            .setMessage("Kody włączone. Ukryte postacie odblokowane.")
                            .setPositiveButton("Graj", null).show();
                    }
                } catch (java.io.IOException | org.json.JSONException error) {
                    Toast.makeText(this, "Nie zapisano ustawień: " + error.getMessage(),
                        Toast.LENGTH_LONG).show();
                }
            }));
        dialog.show();
    }
    @SuppressLint("MissingPermission") // Explicit runtime gate below; no discovery or location access.
    private void connect(boolean host) {
        if (Build.VERSION.SDK_INT >= 31 && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT}, 4202);
            status.setText("Zezwól na połączenie z urządzeniami w pobliżu, a następnie wybierz tryb ponownie.");
            return;
        }
        BluetoothManager manager = (BluetoothManager)getSystemService(BLUETOOTH_SERVICE);
        BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
        if (adapter == null) { status.setText("Ten telefon nie udostępnia Bluetooth. Wybierz grę lokalną."); return; }
        try {
            if (!adapter.isEnabled()) {
                startActivityForResult(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 4203);
                status.setText("Włącz Bluetooth i ponownie wybierz tryb."); return;
            }
            if (host) { start(adapter, null); return; }
            List<BluetoothDevice> peers = new ArrayList<>(adapter.getBondedDevices());
            if (peers.isEmpty()) { status.setText("Brak sparowanych urządzeń. Sparuj oba telefony w ustawieniach Bluetooth."); return; }
            String[] labels = new String[peers.size()];
            for (int i=0; i<peers.size(); i++) {
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
        if (role == null) { BluetoothSession.closeCurrent(); session = null; }
        Intent game = new Intent(this, OpenLF2Activity.class);
        if (role != null) { game.putExtra("bluetooth_role", role); game.putExtra("bluetooth_port", port); }
        transferred = true; startActivity(game); finish();
    }
    @Override protected void onDestroy() {
        if (!transferred && session != null) session.close();
        super.onDestroy();
    }
}
