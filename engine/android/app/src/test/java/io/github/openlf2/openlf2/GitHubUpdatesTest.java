package io.github.openlf2.openlf2;
import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class) @Config(sdk=28)
public class GitHubUpdatesTest {
    @org.junit.Before public void reset() { GitHubUpdates.resetForTest(); }
    private String release(String version,String asset,boolean draft) {
        return "[{\"name\":\"Polish Fighters "+version+"\",\"draft\":"+draft+
            ",\"prerelease\":true,\"html_url\":\"https://github.com/w4sy1/polish-fighters/releases/tag/test\",\"assets\":[{\"name\":\""+asset+"\",\"state\":\"uploaded\"}]}]";
    }
    @Test public void currentAndOlderDoNotNotify() throws Exception {
        assertNull(GitHubUpdates.select(release("0.10.0","Android.apk",false),"0.11.0-local"));
        assertNull(GitHubUpdates.select(release("0.11.0","Android.apk",false),"0.11.0-local"));
    }
    @Test public void uploadedAndroidPrereleaseNotifies() throws Exception {
        assertNotNull(GitHubUpdates.select(release("0.12.0","Android.apk",false),"0.11.0-local"));
    }
    @Test public void draftsAndWrongAssetsDoNotNotify() throws Exception {
        assertNull(GitHubUpdates.select(release("0.12.0","Windows.zip",false),"0.11.0"));
        assertNull(GitHubUpdates.select(release("0.12.0","Android.apk",true),"0.11.0"));
    }
    @Test public void untrustedLinkAndEmptyListDoNotNotify() throws Exception {
        assertNull(GitHubUpdates.select(release("0.12.0","Android.apk",false).replace("github.com/w4sy1/polish-fighters","evil.invalid"),"0.11.0"));
        assertNull(GitHubUpdates.select("[]","0.11.0"));
    }
    @Test(expected=org.json.JSONException.class) public void malformedResponseIsRejected() throws Exception {
        GitHubUpdates.select("not json","0.11.0");
    }
    @Test public void notificationOpensTrustedReleaseAndOnlyAppearsOnce() throws Exception {
        try (org.robolectric.android.controller.ActivityController<android.app.Activity> controller=
                 org.robolectric.Robolectric.buildActivity(android.app.Activity.class).setup()) {
            android.app.Activity activity=controller.get();
            GitHubUpdates.source=()->release("99.0.0","Android.apk",false);
            GitHubUpdates.attach(activity);
            android.app.AlertDialog dialog=null;
            for (int i=0;i<100 && dialog==null;i++) {
                Thread.sleep(10);
                org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
                dialog=org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
            }
            assertNotNull(dialog);
            assertTrue(dialog.isShowing());
            dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).performClick();
            org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
            android.content.Intent opened=org.robolectric.Shadows.shadowOf(activity).getNextStartedActivity();
            assertEquals("https://github.com/w4sy1/polish-fighters/releases/tag/test",opened.getDataString());
            GitHubUpdates.attach(activity);
            assertSame(dialog,org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog());
        }
    }
}
