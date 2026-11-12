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
    private Button moduleButton;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        GitHubUpdates.attach(this);
        setContentView(R.layout.activity_game_home);
        status = findViewById(R.id.pf_status);
        moduleButton = findViewById(R.id.pf_module);
        moduleButton.setOnClickListener(v -> showModules());
        Button play = findViewById(R.id.pf_play);
        Button network = findViewById(R.id.pf_network);
        Button settings = findViewById(R.id.pf_settings);
        java.util.Collections.addAll(actions, moduleButton, play, network, settings);
        play.setOnClickListener(v -> launch(null, 0));
        network.setOnClickListener(v -> showConnections());
        settings.setOnClickListener(v -> showSettings());
        refreshModuleLabel();
        Button cancel = findViewById(R.id.pf_cancel);
        cancel.setOnClickListener(v -> {
            BluetoothSession.closeCurrent(); session = null;
            for (Button action : actions) action.setEnabled(true);
            cancel.setVisibility(android.view.View.GONE);
            status.setText(R.string.pf_ready);
        });
    }
    private void showConnections() {
        new AlertDialog.Builder(this).setTitle(R.string.pf_network)
            .setItems(R.array.pf_connections, (dialog, which) -> {
                if (which == 0) showLan(false);
                else if (which == 1) showLan(true);
                else if (which == 2) connect(true);
                else if (which == 3) connect(false);
                else {
                    try { startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)); }
                    catch (android.content.ActivityNotFoundException absent) { status.setText("Otwórz ustawienia Bluetooth telefonu i sparuj oba telefony."); }
                }
            }).setNegativeButton("Powrót", null).show();
    }
    private void showLan(boolean bluetoothPan) {
        new AlertDialog.Builder(this).setTitle(bluetoothPan ? "Hotspot Bluetooth / PAN" : "Wi-Fi / hotspot")
            .setMessage(bluetoothPan
                ? "Najpierw w ustawieniach systemu włącz udostępnianie Internetu przez Bluetooth i połącz drugie urządzenie z tą siecią. To połączenie TCP po IP, odrębne od próbnego Bluetooth dwóch telefonów. Działa tylko, jeśli oba systemy obsługują PAN."
                : "Połącz oba urządzenia z tym samym Wi-Fi lub hotspotem. Gospodarz wybiera UTWÓRZ POKÓJ. Drugie urządzenie wybiera DOŁĄCZ i wpisuje IPv4 gospodarza oraz ten sam port TCP.")
            .setPositiveButton("Utwórz pokój", (d, w) -> lanAddress(true))
            .setNeutralButton("Dołącz", (d, w) -> lanAddress(false))
            .setNegativeButton("Powrót", null).show();
    }
    private void lanAddress(boolean host) {
        LinearLayout fields = new LinearLayout(this); fields.setOrientation(LinearLayout.VERTICAL);
        TextView help = new TextView(this);
        StringBuilder addresses = new StringBuilder();
        try {
            java.util.Enumeration<java.net.NetworkInterface> interfaces = java.net.NetworkInterface.getNetworkInterfaces();
            while (interfaces != null && interfaces.hasMoreElements()) {
                java.net.NetworkInterface network = interfaces.nextElement();
                if (!network.isUp() || network.isLoopback()) continue;
                java.util.Enumeration<java.net.InetAddress> values = network.getInetAddresses();
                while (values.hasMoreElements()) {
                    java.net.InetAddress value = values.nextElement();
                    if (value instanceof java.net.Inet4Address && value.isSiteLocalAddress())
                        addresses.append(network.getName()).append(": ").append(value.getHostAddress()).append('\n');
                }
            }
        } catch (java.net.SocketException error) { addresses.append("Nie można odczytać adresów.\n"); }
        help.setText((host ? "Podaj drugiemu urządzeniu adres interfejsu wspólnej sieci:\n" + addresses
            : "IP gospodarza: Windows → Ustawienia sieci → Właściwości → IPv4 (lub ipconfig). Telefon → UTWÓRZ POKÓJ.\n")
            + "Domyślny port TCP: 12345. Zapora gospodarza musi zezwalać grze na połączenia w sieci prywatnej.");
        fields.addView(help);
        android.widget.EditText address = new android.widget.EditText(this);
        address.setHint("IPv4 gospodarza"); address.setInputType(android.text.InputType.TYPE_CLASS_PHONE);
        if (!host) fields.addView(address);
        android.widget.EditText port = new android.widget.EditText(this);
        port.setInputType(android.text.InputType.TYPE_CLASS_NUMBER); port.setText("12345"); fields.addView(port);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(host ? "Utwórz pokój" : "Dołącz do pokoju")
            .setView(fields).setPositiveButton("Dalej", null).setNegativeButton("Powrót", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            try {
                int number = Integer.parseInt(port.getText().toString());
                String ip = address.getText().toString().trim();
                GameLaunchArguments.lan(getFilesDir(), host, ip, number);
                BluetoothSession.closeCurrent(); session = null;
                Intent game = new Intent(this, OpenLF2Activity.class);
                game.putExtra("lan_host", host); game.putExtra("lan_address", ip); game.putExtra("lan_port", number);
                transferred = true; startActivity(game); finish(); dialog.dismiss();
            } catch (Exception error) { help.setText("Nie można rozpocząć: " + error.getMessage()); }
        }));
        dialog.show();
    }
    private void refreshModuleLabel() {
        try { moduleButton.setText("MODUŁ: " + new GamePackSettings(getFilesDir()).label()); }
        catch (java.io.IOException | org.json.JSONException error) {
            status.setText("Nie można odczytać wyboru modułów: " + error.getMessage());
        }
    }

    private void showModules() {
        GamePackSettings settings = new GamePackSettings(getFilesDir());
        String[] labels = java.util.Arrays.copyOf(GamePackSettings.TITLES, GamePackSettings.TITLES.length + 2);
        labels[labels.length - 2] = "Wszystkie razem";
        labels[labels.length - 1] = "Dobierz własny zestaw…";
        new AlertDialog.Builder(this).setTitle("Wybierz moduł gry")
            .setItems(labels, (dialog, which) -> {
                if (which == labels.length - 1) { showCustomModules(); return; }
                try {
                    settings.save(which == labels.length - 2 ? GamePackSettings.ALL : GamePackSettings.IDS[which],
                        settings.selection(), settings.hideDuplicates());
                    refreshModuleLabel();
                } catch (java.io.IOException | org.json.JSONException | IllegalArgumentException error) {
                    Toast.makeText(this, "Nie zapisano modułu: " + error.getMessage(), Toast.LENGTH_LONG).show();
                }
            }).setNegativeButton("Anuluj", null).show();
    }

    private void showCustomModules() {
        GamePackSettings settings = new GamePackSettings(getFilesDir());
        final boolean[] selected;
        try { selected = settings.selection(); }
        catch (java.io.IOException | org.json.JSONException error) {
            Toast.makeText(this, "Nie można odczytać modułów: " + error.getMessage(), Toast.LENGTH_LONG).show();
            return;
        }
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Dobierz moduły do wspólnej puli")
            .setMultiChoiceItems(GamePackSettings.TITLES, selected, (window, which, checked) -> selected[which] = checked)
            .setPositiveButton("Zapisz", null).setNegativeButton("Anuluj", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
            try {
                settings.save(GamePackSettings.CUSTOM, selected, settings.hideDuplicates());
                refreshModuleLabel(); dialog.dismiss();
            } catch (java.io.IOException | org.json.JSONException | IllegalArgumentException error) {
                Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
            }
        }));
        dialog.show();
    }
    private void showSettings() {
        final MobileCodeSettings settings = new MobileCodeSettings(getFilesDir());
        final CheckBox codes = new CheckBox(this);
        codes.setText("Włącz kody — odblokuj ukryte postacie");
        codes.setPadding(32, 24, 32, 24);
        final GamePackSettings packs = new GamePackSettings(getFilesDir());
        final CheckBox duplicates = new CheckBox(this);
        duplicates.setText("Ukryj powtórzenia podstawowych postaci we wspólnej puli");
        duplicates.setPadding(32, 12, 32, 24);
        try { codes.setChecked(settings.enabled()); }
        catch (java.io.IOException | org.json.JSONException error) {
            new AlertDialog.Builder(this).setTitle("Błąd ustawień")
                .setMessage("Nie można odczytać ustawień: " + error.getMessage())
                .setPositiveButton("OK", null).show();
            return;
        }
        try { duplicates.setChecked(packs.hideDuplicates()); }
        catch (java.io.IOException | org.json.JSONException error) {
            Toast.makeText(this, "Nie można odczytać ustawień: " + error.getMessage(), Toast.LENGTH_LONG).show();
            return;
        }
        LinearLayout content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);
        content.addView(codes); content.addView(duplicates);
        TextView touchLabel = new TextView(this); touchLabel.setText("Sterowanie dotykowe (wszystkie moduły)");
        content.addView(touchLabel);
        android.widget.Spinner touch = new android.widget.Spinner(this);
        android.widget.ArrayAdapter<String> layouts = new android.widget.ArrayAdapter<>(this,
            android.R.layout.simple_spinner_item, new String[]{"1. Klasyczny LF", "2. Joystick"});
        layouts.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item); touch.setAdapter(layouts);
        try { touch.setSelection("modern".equals(settings.touchLayout()) ? 1 : 0); }
        catch (java.io.IOException | org.json.JSONException error) {
            Toast.makeText(this, "Nie można odczytać sterowania: " + error.getMessage(), Toast.LENGTH_LONG).show(); return;
        }
        content.addView(touch);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Ustawienia")
            .setView(content).setPositiveButton("Zapisz", null)
            .setNegativeButton("Anuluj", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(view -> {
                try {
                    boolean wasEnabled = settings.enabled();
                    settings.save(codes.isChecked(), duplicates.isChecked(), touch.getSelectedItemPosition()==1 ? "modern" : "classic");
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
