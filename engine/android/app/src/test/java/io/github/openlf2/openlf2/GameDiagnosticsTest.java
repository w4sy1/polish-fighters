package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowAlertDialog;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28)
public class GameDiagnosticsTest {
    @Test public void secretsAndUrlsAreRedacted() {
        String text=GameDiagnostics.redact("TOKEN=private Password: hidden Bearer sensitive https://example.test/?secret=one");
        assertFalse(text.contains("private"));assertFalse(text.contains("hidden"));
        assertFalse(text.contains("sensitive"));assertFalse(text.contains("example.test"));
    }
    @Test public void localFileIsBoundedAndNoSettingsSecretsAreCopied() throws Exception {
        Context context=RuntimeEnvironment.getApplication();
        GameDiagnostics.write(context,"java-last.txt","token=hide " + new String(new char[90000]).replace('\0','x'));
        File report=new File(context.getFilesDir(),"diagnostics/java-last.txt");
        assertTrue(report.isFile());assertTrue(report.length()<=65536);
        File directory=new File(context.getFilesDir(),"settings");directory.mkdirs();
        File config=new File(directory,"config.json");
        Files.write(config.toPath(),("{\"account\":{\"token\":\"private-account-secret\"},"
            +"\"polish_fighters_last_crash\":{\"stage\":12,\"profile\":\"lf4-turbo\"}}").getBytes(StandardCharsets.UTF_8));
        String text=GameDiagnostics.report(context);
        assertTrue(text.contains("lf4-turbo"));assertFalse(text.contains("private-account-secret"));
        assertFalse(text.contains("token=hide"));
    }
    @Test public void sharingRequiresTheUserButton() {
        Activity activity=Robolectric.buildActivity(Activity.class).setup().get();
        GameDiagnostics.show(activity);
        assertNull(Shadows.shadowOf(activity).getNextStartedActivity());
        AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).performClick();
        Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        Intent chooser=Shadows.shadowOf(activity).getNextStartedActivity();
        assertEquals(Intent.ACTION_CHOOSER,chooser.getAction());
        activity.finish();
    }
}
