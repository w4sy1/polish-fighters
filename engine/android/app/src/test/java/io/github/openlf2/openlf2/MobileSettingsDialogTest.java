package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.app.AlertDialog;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowAlertDialog;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class MobileSettingsDialogTest {
    @org.junit.Before public void disableUpdateNetwork() { GitHubUpdates.resetForTest(); }
    private View find(View root, Class<?> type, String text) {
        if (type.isInstance(root) && (text == null
                || (root instanceof Button && text.equals(((Button)root).getText().toString())))) return root;
        if (root instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)root;
            for (int i = 0; i < group.getChildCount(); i++) {
                View result = find(group.getChildAt(i), type, text);
                if (result != null) return result;
            }
        }
        return null;
    }

    @Test public void enablingFromSettingsPersistsAndShowsLamus() throws Exception {
        try (ActivityController<BluetoothLobbyActivity> controller =
                Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()) {
            BluetoothLobbyActivity activity = controller.get();
            new MobileCodeSettings(activity.getFilesDir()).save(false);
            View open = find(activity.getWindow().getDecorView(), Button.class, "USTAWIENIA");
            assertNotNull(open);
            open.performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            AlertDialog menu = ShadowAlertDialog.getLatestAlertDialog();
            android.widget.ListView list=menu.getListView();list.performItemClick(list.getAdapter().getView(2,null,list),2,2);
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            AlertDialog settings = ShadowAlertDialog.getLatestAlertDialog();
            CheckBox checkbox = (CheckBox)find(settings.getWindow().getDecorView(), CheckBox.class, null);
            assertNotNull(checkbox);
            assertFalse(checkbox.isChecked());
            checkbox.performClick();
            assertFalse(new MobileCodeSettings(activity.getFilesDir()).enabled());
            settings.getButton(AlertDialog.BUTTON_POSITIVE).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            assertTrue(new MobileCodeSettings(activity.getFilesDir()).enabled());
            AlertDialog message = ShadowAlertDialog.getLatestAlertDialog();
            assertEquals("lamus", Shadows.shadowOf(message).getTitle().toString());
            assertTrue(message.isShowing());
        }
    }

    @Test public void cancelDoesNotEnableCodes() throws Exception {
        try (ActivityController<BluetoothLobbyActivity> controller =
                Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()) {
            BluetoothLobbyActivity activity = controller.get();
            new MobileCodeSettings(activity.getFilesDir()).save(false);
            find(activity.getWindow().getDecorView(), Button.class, "USTAWIENIA").performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            AlertDialog menu = ShadowAlertDialog.getLatestAlertDialog();
            android.widget.ListView list=menu.getListView();list.performItemClick(list.getAdapter().getView(2,null,list),2,2);
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            AlertDialog settings = ShadowAlertDialog.getLatestAlertDialog();
            ((CheckBox)find(settings.getWindow().getDecorView(), CheckBox.class, null)).performClick();
            settings.getButton(AlertDialog.BUTTON_NEGATIVE).performClick();
            Shadows.shadowOf(Looper.getMainLooper()).idle();
            assertFalse(new MobileCodeSettings(activity.getFilesDir()).enabled());
        }
    }
}
