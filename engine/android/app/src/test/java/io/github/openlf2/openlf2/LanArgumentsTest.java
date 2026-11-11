package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import java.io.File;
import java.util.Arrays;
import java.util.List;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28, manifest = Config.NONE)
public class LanArgumentsTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();
    private File ready() throws Exception {
        File game = new File(temporary.getRoot(), "game"); game.mkdirs();
        new File(game, ".ready").createNewFile(); return temporary.getRoot();
    }
    @Test public void hostListensOnLanAndUsesRoomProtocol() throws Exception {
        List<String> args=Arrays.asList(GameLaunchArguments.lan(ready(),true,"",12345));
        assertTrue(args.contains("--room")); assertEquals("0.0.0.0",args.get(args.indexOf("--host")+1));
        assertFalse(args.stream().anyMatch(v -> v.endsWith("bluetooth-room")));
    }
    @Test public void joinUsesRemoteAddressAndPortWithoutBluetoothDecorator() throws Exception {
        List<String> args=Arrays.asList(GameLaunchArguments.lan(ready(),false,"192.168.1.82",23456));
        assertEquals("192.168.1.82",args.get(args.indexOf("--join")+1));
        assertEquals("23456",args.get(args.indexOf("--port")+1));
        assertFalse(args.contains("127.0.0.1"));
    }
    @Test public void badAddressesAndPortsAreRejected() throws Exception {
        File root=ready();
        for(String ip:new String[]{"127.0.0.1","0.0.0.0","256.1.1.1","1.2.3","1.2.3.","host"}) {
            try {GameLaunchArguments.lan(root,false,ip,12345);fail(ip);} catch(IllegalArgumentException expected) {}
        }
        for(int port:new int[]{0,-1,65536}) {
            try {GameLaunchArguments.lan(root,true,"",port);fail();} catch(IllegalArgumentException expected) {}
        }
    }
    @Test public void touchChoiceSurvivesReloadAndPreservesOtherSettings() throws Exception {
        MobileCodeSettings store=new MobileCodeSettings(temporary.getRoot());
        store.write(new org.json.JSONObject("{\"controls\":{\"keep\":true},\"progress\":7}"));
        store.save(false,true,"modern");
        assertEquals("modern",new MobileCodeSettings(temporary.getRoot()).touchLayout());
        assertTrue(store.read().getJSONObject("controls").getBoolean("keep"));
        assertEquals(7,store.read().getInt("progress"));
        store.save(true,false,"classic"); assertEquals("classic",store.touchLayout());
    }
}
