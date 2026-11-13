package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.rules.TemporaryFolder;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34)
public class AndroidModPackageImporterTest {
    @Rule public TemporaryFolder temporary=new TemporaryFolder();
    private static final String ID="mod-0123456789abcdef01234567";

    private byte[] archive(String extraName) throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try(ZipOutputStream zip=new ZipOutputStream(bytes)) {
            put(zip,"pack/package.manifest","id="+ID+"\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/game/catalog|catalog.lua\nextend=base/game/sounds|sounds.lua\nasset=mods/"+ID+"/a/000000.dat|assets/a/000000.dat\n");
            put(zip,"pack/catalog.lua","return function(base)\n base.source_path=\"mods/"+ID+"/a/000000.dat\"\n base.stage_path=\"mods/"+ID+"/a/000000.dat\"\n base.profile_id=\""+ID+"\"\n return base\nend\n");
            put(zip,"pack/sounds.lua","return function(base)\n local paths={\n }\n for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end\n for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end\n return base\nend\n");
            put(zip,"pack/assets/a/000000.dat","<object></object>\n");
            if(extraName!=null)put(zip,"pack/"+extraName,"blocked");
        }
        return bytes.toByteArray();
    }
    private static void put(ZipOutputStream zip,String name,String content)throws Exception {zip.putNextEntry(new ZipEntry(name));zip.write(content.getBytes(StandardCharsets.UTF_8));zip.closeEntry();}
    private File readyRoot() throws Exception {File root=temporary.newFolder("files");File game=new File(root,"game");assertTrue(game.mkdirs());assertTrue(new File(game,".ready").createNewFile());return root;}

    @Test public void importsOnlyConverterPackageAndMakesItSelectable() throws Exception {
        File root=readyRoot();
        assertEquals(ID,AndroidModPackageImporter.importPackage(new ByteArrayInputStream(archive(null)),root,null));
        File installed=new File(root,"game/content-packs/"+ID);
        assertTrue(new File(installed,"package.manifest").isFile());
        assertTrue(new File(installed,"assets/a/000000.dat").isFile());
        GamePackSettings settings=new GamePackSettings(root);settings.save(ID,settings.selection(),true);
        assertEquals(ID,settings.mode());assertTrue(settings.imported().contains(ID));
        assertTrue(java.util.Arrays.asList(GameLaunchArguments.build(root,null,0)).contains(installed.getAbsolutePath()));
    }

    @Test public void rejectsExecutablesAndTraversalWithoutPartialInstall() throws Exception {
        for(String unsafe:new String[]{"setup.exe","bin/evil.dll","../outside.dat"}) {
            File root=readyRoot();
            try {AndroidModPackageImporter.importPackage(new ByteArrayInputStream(archive(unsafe)),root,null);fail("accepted "+unsafe);}
            catch(IOException expected) {}
            File packs=new File(root,"game/content-packs");
            assertEquals(0,packs.listFiles().length);
        }
    }

    @Test public void refusesUnpreparedGame() throws Exception {
        File root=temporary.newFolder("empty");
        try {AndroidModPackageImporter.importPackage(new ByteArrayInputStream(archive(null)),root,null);fail();}
        catch(IOException expected) {assertTrue(expected.getMessage().contains("przygotuj"));}
    }
}
