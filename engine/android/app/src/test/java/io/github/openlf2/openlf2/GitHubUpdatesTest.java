package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class) @Config(sdk=28)
public class GitHubUpdatesTest {
    private static final String REPOSITORY = "https://github.com/w4sy1/polish-fighters/releases/";
    private static final String[] ARM = {"arm64-v8a"};

    private JSONObject asset(String version, String name) throws Exception {
        return new JSONObject().put("name", name).put("state", "uploaded")
            .put("browser_download_url", REPOSITORY + "download/v" + version + "/" + name);
    }

    private JSONObject release(String version, String abi, boolean draft, boolean checksum) throws Exception {
        String name = "PolishFighters-Android-" + abi + ".apk";
        JSONArray assets = new JSONArray().put(asset(version, name));
        if (checksum) assets.put(asset(version, name + ".sha256"));
        return new JSONObject().put("name", "Polish Fighters " + version).put("tag_name", "v" + version)
            .put("draft", draft).put("html_url", REPOSITORY + "tag/v" + version).put("assets", assets);
    }

    @Test public void selectsNewestCompletePackageForPreferredAbi() throws Exception {
        JSONObject both = release("0.19.0", "arm64-v8a", false, true);
        both.getJSONArray("assets").put(asset("0.19.0", "PolishFighters-Android-x86_64.apk"))
            .put(asset("0.19.0", "PolishFighters-Android-x86_64.apk.sha256"));
        JSONArray releases = new JSONArray().put(release("0.21.0", "arm64-v8a", true, true))
            .put(release("0.20.0", "arm64-v8a", false, false)).put(both)
            .put(release("0.18.15", "x86_64", false, true));
        GitHubUpdates.Candidate candidate = GitHubUpdates.select(releases.toString(), "0.18.14",
            new String[]{"arm64-v8a", "x86_64"});
        assertNotNull(candidate);
        assertEquals("v0.19.0", candidate.version);
        assertEquals("PolishFighters-Android-arm64-v8a.apk", candidate.name);
        assertEquals(candidate.apk + ".sha256", candidate.checksum);
    }

    @Test public void rejectsOlderWrongAbiAndUntrustedAssets() throws Exception {
        JSONObject untrusted = release("0.22.0", "arm64-v8a", false, true);
        untrusted.getJSONArray("assets").getJSONObject(0).put("browser_download_url", "https://other.example/game.apk");
        JSONArray releases = new JSONArray().put(release("0.18.14", "arm64-v8a", false, true))
            .put(release("0.21.0", "x86_64", false, true)).put(untrusted);
        assertNull(GitHubUpdates.select(releases.toString(), "0.18.14", ARM));
    }

    @Test(expected=org.json.JSONException.class) public void malformedResponseIsRejected() throws Exception {
        GitHubUpdates.select("not json", "0.18.14", ARM);
    }
}
