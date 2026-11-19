package io.github.openlf2.openlf2;

import static org.junit.Assert.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
public class SignedModPackageTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();
    private final Ed25519PrivateKeyParameters signer = new Ed25519PrivateKeyParameters(new SecureRandom());

    @Test public void installsAndExposesSignedModToGame() throws Exception {
        File root = readyRoot();
        String id = install(root, envelope(false, false, false));
        assertEquals("mod-" + hash(bytes("signed:arena")).substring(0, 24), id);
        File module = new File(root, "game/content-packs/" + id);
        assertTrue(new File(module, "catalog.lua").isFile());
        assertTrue(new File(module, "assets/a/stage.dat").isFile());
        GamePackSettings settings = new GamePackSettings(root);
        settings.save(id, settings.selection(), settings.hideDuplicates());
        assertTrue(settings.imported().contains(id));
        assertTrue(java.util.Arrays.asList(GameLaunchArguments.build(root, null, 0))
                .contains(module.getAbsolutePath()));
    }

    @Test public void rejectsBadSignatureHashAndLuaWithoutPublishing() throws Exception {
        for (byte[] envelope : new byte[][] {
                envelope(true, false, false), envelope(false, true, false), envelope(false, false, true)}) {
            File root = readyRoot();
            assertThrows(IOException.class, () -> install(root, envelope));
            assertEquals(0, new File(root, "game/content-packs").list().length);
        }
    }

    @Test public void playRejectsLegacyImportsBeforeAnyExtraction() throws Exception {
        ByteArrayOutputStream archive = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(archive)) {
            put(zip, "pack/catalog.lua", bytes("return 1"));
        }
        File root = readyRoot();
        IOException error = assertThrows(IOException.class, () -> install(root, archive.toByteArray()));
        assertTrue(error.getMessage().contains("tylko podpisane"));
        assertEquals(0, new File(root, "game/content-packs").list().length);
    }

    private String install(File root, byte[] input) throws IOException {
        return AndroidModPackageImporter.importPackage(new ByteArrayInputStream(input), root,
                () -> signer.generatePublicKey().getEncoded(), "1.1.1", true, null);
    }

    private File readyRoot() throws IOException {
        File root = temporary.newFolder();
        File game = new File(root, "game");
        assertTrue(game.mkdir());
        assertTrue(new File(game, ".ready").createNewFile());
        return root;
    }

    private byte[] envelope(boolean badSignature, boolean badHash, boolean lua) throws Exception {
        byte[] recipe = bytes("{\"source\":\"assets/a/data.txt\",\"stage\":\"assets/a/stage.dat\"}");
        byte[] data = bytes("<object>\n<object_end>\n");
        byte[] stage = bytes("game data");
        byte[] script = bytes("return 1");
        ByteArrayOutputStream inner = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(inner)) {
            put(zip, "module.json", recipe);
            put(zip, "assets/a/data.txt", data);
            put(zip, "assets/a/stage.dat", stage);
            if (lua) put(zip, "assets/a/script.lua", script);
        }
        byte[] payload = inner.toByteArray();
        long expanded = recipe.length + data.length + stage.length + (lua ? script.length : 0);
        byte[] manifest = bytes("{\"author\":\"Test\",\"category\":\"areny\",\"conflicts\":[],\"dependencies\":[],"
                + "\"id\":\"arena\",\"installation\":{\"entrypoint\":\"module.json\",\"method\":\"managed-data-zip\"},"
                + "\"license\":\"CC-BY-4.0\",\"min_engine_version\":\"1.1.0\",\"name\":\"Arena\",\"package_type\":\"data-only\","
                + "\"platforms\":[\"windows\",\"android\"],\"required_assets\":[],\"schema_version\":2,"
                + "\"sha256\":\"" + (badHash ? hash(bytes("wrong")) : hash(payload)) + "\",\"size_bytes\":" + payload.length
                + ",\"source\":{\"type\":\"github-release-asset\",\"url\":\"https://github.com/w4sy1/polish-fighters-mody/releases/download/arena-v1.0.0/arena.zip\"},"
                + "\"test_status\":{\"android\":\"pending\",\"windows\":\"pending\"},\"unpacked_size_bytes\":"
                + expanded + ",\"version\":\"1.0.0\"}");
        byte[] index = bytes("{\"channel\":\"stable\",\"manifests\":{\"arena@1.0.0\":\""
                + hash(manifest) + "\"},\"revision\":1}");
        ByteArrayOutputStream outer = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(outer)) {
            put(zip, "catalog.json", index);
            put(zip, "catalog.sig", sign(index));
            put(zip, "manifest.json", manifest);
            put(zip, "manifest.sig", badSignature ? new byte[64] : sign(manifest));
            put(zip, "package.zip", payload);
        }
        return outer.toByteArray();
    }

    private byte[] sign(byte[] data) {
        Ed25519Signer signature = new Ed25519Signer();
        signature.init(true, signer);
        signature.update(data, 0, data.length);
        return signature.generateSignature();
    }

    private static String hash(byte[] data) throws Exception {
        StringBuilder hex = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(data))
            hex.append(String.format(Locale.ROOT, "%02x", b & 255));
        return hex.toString();
    }

    private static byte[] bytes(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }

    private static void put(ZipOutputStream zip, String name, byte[] contents) throws IOException {
        zip.putNextEntry(new ZipEntry(name));
        zip.write(contents);
        zip.closeEntry();
    }
}
