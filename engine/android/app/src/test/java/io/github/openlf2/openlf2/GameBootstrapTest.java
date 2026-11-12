package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import org.junit.*;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowStatFs;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28, shadows=GameBootstrapTest.FileSystemShadow.class)
public class GameBootstrapTest {
 @Rule public TemporaryFolder temporary=new TemporaryFolder();
 private String hash(byte[] bytes) throws Exception {
  StringBuilder value=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))value.append(String.format(Locale.ROOT,"%02x",b&255));return value.toString();
 }
 private Map<String,byte[]> fixture(boolean first, String path) throws Exception {
  byte[] payload="working game".getBytes(StandardCharsets.UTF_8);String digest=hash(payload);
  byte[] manifest=new JSONObject().put("schema",1).put("files",new JSONArray().put(new JSONObject().put("path",path).put("bytes",payload.length).put("sha256",digest))).toString().getBytes(StandardCharsets.UTF_8);
  ByteArrayOutputStream output=new ByteArrayOutputStream();
  try(ZipOutputStream zip=new ZipOutputStream(output)) {
   if(first){zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(manifest);zip.closeEntry();}
   zip.putNextEntry(new ZipEntry("blobs/"+digest));zip.write(payload);zip.closeEntry();
   if(!first){zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(manifest);zip.closeEntry();}
  }
  Map<String,byte[]> files=new HashMap<>();files.put("game-bundle.id",hash(manifest).getBytes(StandardCharsets.US_ASCII));files.put("game-bundle.zip",output.toByteArray());return files;
 }
 private void prepare(Map<String,byte[]> bundle, File root) throws Exception {
  ShadowStatFs.registerStats(root.getPath(),4096,16*1024*1024,16*1024*1024);
  GameBootstrapActivity.prepareBundle(name->{byte[] value=bundle.get(name);if(value==null)throw new FileNotFoundException(name);return new ByteArrayInputStream(value);},root,(linking,current,total)->{});
 }
 @Test public void freshInstallPreparesRealFilesAndReadyMarker() throws Exception {
  File root=temporary.getRoot();Map<String,byte[]> bundle=fixture(true,"scripts/start.lua");prepare(bundle,root);
  assertArrayEquals("working game".getBytes(StandardCharsets.UTF_8),Files.readAllBytes(new File(root,"game/scripts/start.lua").toPath()));
  assertArrayEquals(bundle.get("game-bundle.id"),Files.readAllBytes(new File(root,"game/.ready").toPath()));
 }
 @Test public void exactReportedFailureRejectsManifestAtEnd() throws Exception {
  try{prepare(fixture(false,"scripts/start.lua"),temporary.getRoot());fail("Must reproduce bad published ZIP");}
  catch(IOException expected){assertEquals("Brak indeksu paczki gry.",expected.getMessage());}
  assertFalse(new File(temporary.getRoot(),"game/.ready").exists());
 }
 @Test public void updatePreservesPrivateSettingsAndReusesReadyGame() throws Exception {
  File root=temporary.getRoot();File settings=new File(root,"settings");assertTrue(settings.mkdir());
  File config=new File(settings,"config.json");Files.write(config.toPath(),"keep controls".getBytes(StandardCharsets.UTF_8));
  Map<String,byte[]> bundle=fixture(true,"scripts/start.lua");prepare(bundle,root);
  GameBootstrapActivity.prepareBundle(name->{if(name.equals("game-bundle.id"))return new ByteArrayInputStream(bundle.get(name));throw new IOException("Ready install must not reopen archive");},root,(a,b,c)->{});
  assertEquals("keep controls",new String(Files.readAllBytes(config.toPath()),StandardCharsets.UTF_8));
 }
 @Test public void invalidPathCannotWriteIntoSettings() throws Exception {
  try{prepare(fixture(true,"../settings/config.json"),temporary.getRoot());fail();}
  catch(IOException expected){assertTrue(expected.getMessage().contains("ścieżka"));}
  assertFalse(new File(temporary.getRoot(),"settings/config.json").exists());
 }
 @Test public void realApkInstallsFromEmptyStorage() throws Exception {
  String input=System.getenv("PF_REAL_APK");Assume.assumeTrue("Full APK supplied by release verification",input!=null);
  File root=temporary.getRoot();ShadowStatFs.registerStats(root.getPath(),4096,16*1024*1024,16*1024*1024);
  try(ZipFile apk=new ZipFile(input)) {
   GameBootstrapActivity.prepareBundle(name->{ZipEntry entry=apk.getEntry("assets/"+name);if(entry==null)throw new FileNotFoundException(name);return apk.getInputStream(entry);},root,(a,b,c)->{});
  }
  assertTrue(new File(root,"game/.ready").isFile());
  assertTrue(new File(root,"game/LF2_v2.0a.exe").isFile());
  assertTrue(new File(root,"game/scripts/polish-fighters/hub.lua").isFile());
  assertTrue(new File(root,"game/content-packs/lf4-turbo/package.manifest").isFile());
  assertTrue(Arrays.asList(GameLaunchArguments.build(root,null,0)).contains("--scripts"));
 }
 @Implements(Os.class) public static class FileSystemShadow {
  @Implementation protected static void link(String oldPath,String newPath) throws ErrnoException {
   try{Files.createLink(Paths.get(newPath),Paths.get(oldPath));}catch(IOException error){throw new ErrnoException("link",OsConstants.EXDEV,error);}
  }
  @Implementation protected static void rename(String oldPath,String newPath) throws ErrnoException {
   try{Files.move(Paths.get(oldPath),Paths.get(newPath),StandardCopyOption.REPLACE_EXISTING);}catch(IOException error){throw new ErrnoException("rename",OsConstants.EIO,error);}
  }
 }
}
