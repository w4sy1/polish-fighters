package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.app.AlertDialog;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ListView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowAlertDialog;
import org.robolectric.shadows.ShadowToast;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class GamePackDialogTest {
    private Button moduleButton(View root) {
        if (root instanceof Button && ((Button)root).getText().toString().startsWith("MODUŁ:")) return (Button)root;
        if (root instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)root;
            for (int i = 0; i < group.getChildCount(); i++) {
                Button result = moduleButton(group.getChildAt(i));
                if (result != null) return result;
            }
        }
        return null;
    }

    private void choose(AlertDialog dialog, int position) {
        ListView list = dialog.getListView();
        list.performItemClick(list.getAdapter().getView(position, null, list), position, position);
        Shadows.shadowOf(Looper.getMainLooper()).idle();
    }

    @Test public void singleModuleAndAllCanBeChosenFromActualLobby() throws Exception {
        try (ActivityController<BluetoothLobbyActivity> controller = Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()) {
            BluetoothLobbyActivity activity = controller.get();
            Button open = moduleButton(activity.getWindow().getDecorView());
            assertNotNull(open);
            open.performClick(); Shadows.shadowOf(Looper.getMainLooper()).idle();
            choose(ShadowAlertDialog.getLatestAlertDialog(), 0);
            GamePackSettings settings = new GamePackSettings(activity.getFilesDir());
            assertEquals("polish_fighters", settings.mode());
            assertTrue(open.getText().toString().contains("Polish Fighters"));
            open.performClick(); Shadows.shadowOf(Looper.getMainLooper()).idle();
            choose(ShadowAlertDialog.getLatestAlertDialog(), GamePackSettings.IDS.length);
            assertEquals(GamePackSettings.ALL, settings.mode());
            for (boolean selected : settings.selection()) assertTrue(selected);
        }
    }

    @Test public void customPoolSavesOnlyCheckedModules() throws Exception {
        try (ActivityController<BluetoothLobbyActivity> controller = Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()) {
            BluetoothLobbyActivity activity = controller.get();
            GamePackSettings settings = new GamePackSettings(activity.getFilesDir());
            settings.save(GamePackSettings.ALL, settings.selection(), true);
            moduleButton(activity.getWindow().getDecorView()).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            choose(ShadowAlertDialog.getLatestAlertDialog(), GamePackSettings.IDS.length + 1);
            AlertDialog custom = ShadowAlertDialog.getLatestAlertDialog();
            for (int i = 1; i < GamePackSettings.IDS.length; i++) choose(custom, i);
            custom.getButton(AlertDialog.BUTTON_POSITIVE).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            assertEquals(GamePackSettings.CUSTOM, settings.mode());
            assertTrue(settings.selection()[0]);
            for (int i = 1; i < GamePackSettings.IDS.length; i++) assertFalse(settings.selection()[i]);
        }
    }

    @Test public void emptyCustomPoolShowsErrorAndStaysOpen() throws Exception {
        try (ActivityController<BluetoothLobbyActivity> controller = Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()) {
            BluetoothLobbyActivity activity = controller.get();
            GamePackSettings settings = new GamePackSettings(activity.getFilesDir());
            settings.save(GamePackSettings.ALL, settings.selection(), true);
            moduleButton(activity.getWindow().getDecorView()).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            choose(ShadowAlertDialog.getLatestAlertDialog(), GamePackSettings.IDS.length + 1);
            AlertDialog custom = ShadowAlertDialog.getLatestAlertDialog();
            for (int i = 0; i < GamePackSettings.IDS.length; i++) choose(custom, i);
            custom.getButton(AlertDialog.BUTTON_POSITIVE).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            assertTrue(custom.isShowing());
            assertEquals(GamePackSettings.ALL, settings.mode());
            assertEquals("Wybierz przynajmniej jeden moduł", ShadowToast.getTextOfLatestToast());
        }
    }
}
