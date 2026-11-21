package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.content.Intent;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowBluetoothAdapter;

/** Etap 1.14 / Zadanie 4A.2: BluetoothPairingActivity replaces the old
 *  room/tcp/lan/bluetooth rows that used to live inside the Android tools
 *  screen's "network" dialog (BluetoothLobbyActivity.showConnections) --
 *  that screen keeps serving little_fighters_open_android_tools unchanged
 *  (see StartScreenTest), this is a separate, dedicated pairing screen with
 *  exactly four actions: search (pair), host, join, back. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class BluetoothPairingActivityTest {
    @Test
    public void fourActionsVisibleWithCorrectLabels() {
        try (ActivityController<BluetoothPairingActivity> controller =
                Robolectric.buildActivity(BluetoothPairingActivity.class).setup()) {
            BluetoothPairingActivity activity = controller.get();
            assertEquals("SZUKAJ URZĄDZEŃ", ((Button) activity.findViewById(R.id.pf_module)).getText().toString());
            assertEquals("UTWÓRZ POKÓJ", ((Button) activity.findViewById(R.id.pf_network)).getText().toString());
            assertEquals("DOŁĄCZ", ((Button) activity.findViewById(R.id.pf_settings)).getText().toString());
            assertEquals("WSTECZ", ((Button) activity.findViewById(R.id.pf_quit)).getText().toString());
            assertEquals(View.GONE, activity.findViewById(R.id.pf_cancel).getVisibility());
        }
    }

    @Test
    public void backAlwaysReturnsToOpenLF2ActivityOnRemoteMenu() throws Exception {
        try (ActivityController<BluetoothPairingActivity> controller =
                Robolectric.buildActivity(BluetoothPairingActivity.class).setup()) {
            BluetoothPairingActivity activity = controller.get();
            activity.findViewById(R.id.pf_quit).performClick();
            Intent next = Shadows.shadowOf(activity).getNextStartedActivity();
            assertEquals(OpenLF2Activity.class.getName(), next.getComponent().getClassName());
            assertEquals("remote",
                new MobileCodeSettings(activity.getFilesDir()).read().optString("little_fighters_start_menu"));
        }
    }

    @Test
    public void onBackPressedUsesTheSameRemoteReturnPath() throws Exception {
        try (ActivityController<BluetoothPairingActivity> controller =
                Robolectric.buildActivity(BluetoothPairingActivity.class).setup()) {
            BluetoothPairingActivity activity = controller.get();
            activity.onBackPressed();
            Intent next = Shadows.shadowOf(activity).getNextStartedActivity();
            assertEquals(OpenLF2Activity.class.getName(), next.getComponent().getClassName());
            assertEquals("remote",
                new MobileCodeSettings(activity.getFilesDir()).read().optString("little_fighters_start_menu"));
        }
    }

    @Test
    public void missingAdapterShowsStatusMessage() {
        ShadowBluetoothAdapter.setIsBluetoothSupported(false);
        try (ActivityController<BluetoothPairingActivity> controller =
                Robolectric.buildActivity(BluetoothPairingActivity.class).setup()) {
            BluetoothPairingActivity activity = controller.get();
            String status = ((TextView) activity.findViewById(R.id.pf_status)).getText().toString();
            assertTrue("status must explain the missing Bluetooth adapter: " + status,
                status.contains("Ten telefon nie udostępnia Bluetooth"));
        }
    }
}
