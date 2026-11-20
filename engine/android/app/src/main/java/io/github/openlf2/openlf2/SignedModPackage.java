package io.github.openlf2.openlf2;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.Set;
import java.util.zip.CRC32;
import java.util.zip.CheckedInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipInputStream;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.json.JSONException;
import org.json.JSONObject;

final class SignedModPackage {
    static final String FIRST_ENTRY = "catalog.json";
    static final String KEY_ASSET = "mods/catalog-ed25519.pub";
    private static final int META_LIMIT = 1024 * 1024;
    private static final long ZIP_LIMIT = 256L * 1024 * 1024;
    private static final long TOTAL_LIMIT = 1024L * 1024 * 1024;
    private static final long RESERVE = 64L * 1024 * 1024;
    private static final String ASSET = "assets/a/(?!(con|prn|aux|nul|com[1-9]|lpt[1-9])\\.)[a-z0-9]{1,40}\\.(txt|dat|bmp|png|jpg|jpeg|wav|ogg|mp3|json)";

    static final String CONTENT_PACK = "content-pack";
    private static final long PACK_ZIP_LIMIT = 2047L * 1024 * 1024;
    private static final long PACK_TOTAL_LIMIT = 4L * 1024 * 1024 * 1024;
    private static final int PACK_FILES = 20000;
    private static final String FORBIDDEN = ".*\\.(exe|dll|so|dylib|bat|cmd|ps1|sh|py|com|scr|msi|jar|apk|dex|vbs|js)";

    /** Result of a verified envelope: the module ID and whether it is a full content pack. */
    static final class Prepared {
        final String id, version; final boolean contentPack;
        Prepared(String id, String version, boolean contentPack) {
            this.id = id; this.version = version; this.contentPack = contentPack;
        }
    }

    interface Progress { void update(int done, int total); }

    private SignedModPackage() {}

    static String prepare(ZipInputStream stream, File staging, byte[] key, String engineVersion)
            throws IOException {
        Prepared result = prepare(stream, staging, key, engineVersion, null, null);
        if (result.contentPack) throw new IOException("Pełną paczkę instaluje ekran Mody.");
        return result.id;
    }

    static Prepared prepare(ZipInputStream stream, File staging, byte[] key, String engineVersion,
            String expectedId, Progress progress) throws IOException {
        try {
            byte[] index = read(stream, META_LIMIT);
            expect(stream, "catalog.sig");
            JSONObject catalog = signed(index, read(stream, 64), key);
            if (!"stable".equals(catalog.getString("channel")) || catalog.getLong("revision") < 1)
                throw new IOException("Nieprawidłowy indeks STABLE.");
            expect(stream, "manifest.json");
            byte[] manifestBytes = read(stream, META_LIMIT);
            expect(stream, "manifest.sig");
            JSONObject manifest = signed(manifestBytes, read(stream, 64), key);
            String id = manifest.getString("id");
            String version = manifest.getString("version");
            String minimum = manifest.getString("min_engine_version");
            JSONObject installation = manifest.getJSONObject("installation");
            boolean contentPack = CONTENT_PACK.equals(manifest.getString("package_type"));
            if (manifest.getInt("schema_version") != 2 || !id.matches("[a-z0-9]+(-[a-z0-9]+)*")
                    || id.length() > 64 || id.startsWith("mod-")
                    || !version.matches("(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)")
                    || !(contentPack ? "content-pack-zip".equals(installation.getString("method"))
                            && "package.manifest".equals(installation.getString("entrypoint"))
                        : "data-only".equals(manifest.getString("package_type"))
                            && "managed-data-zip".equals(installation.getString("method"))
                            && "module.json".equals(installation.getString("entrypoint"))))
                throw new IOException("Nieobsługiwany manifest podpisanej paczki.");
            if (expectedId != null && !expectedId.equals(id))
                throw new IOException("Pobrany plik zawiera inny moduł niż wybrany.");
            if (!atLeast(engineVersion, minimum))
                throw new IOException("Paczka wymaga nowszej wersji silnika.");
            boolean android = false;
            for (int i = 0; i < manifest.getJSONArray("platforms").length(); i++)
                android |= "android".equals(manifest.getJSONArray("platforms").getString(i));
            if (!android || manifest.getJSONArray("dependencies").length() != 0
                    || manifest.getJSONArray("conflicts").length() != 0
                    || manifest.getJSONArray("required_assets").length() != 0)
                throw new IOException("Paczka nie wspiera Androida lub wymaga dodatkowych zasobów.");
            String pin = catalog.getJSONObject("manifests").optString(id + "@" + version);
            if (!hex(digest().digest(manifestBytes)).equals(pin))
                throw new IOException("Manifest nie figuruje w zaufanym indeksie.");
            long size = manifest.getLong("size_bytes");
            long unpacked = manifest.getLong("unpacked_size_bytes");
            if (size < 1 || size > (contentPack ? PACK_ZIP_LIMIT : ZIP_LIMIT) || unpacked < 1
                    || unpacked > (contentPack ? PACK_TOTAL_LIMIT : TOTAL_LIMIT))
                throw new IOException("Paczka przekracza limit rozmiaru.");
            if (staging.getFreeSpace() < size + unpacked + RESERVE)
                throw new IOException("Za mało wolnego miejsca na podpisaną paczkę.");
            expect(stream, "package.zip");
            File payload = new File(staging, ".payload.zip");
            MessageDigest hash = digest();
            try (FileOutputStream output = new FileOutputStream(payload)) {
                if (copy(stream, output, size, hash) != size)
                    throw new IOException("Niezgodny rozmiar paczki.");
            }
            if (!hex(hash.digest()).equals(manifest.getString("sha256")) || stream.getNextEntry() != null)
                throw new IOException("Niezgodny SHA-256 lub nadmiarowe wpisy paczki.");
            if (contentPack) {
                unpackContentPack(payload, staging, id, unpacked, progress);
                if (!payload.delete()) throw new IOException("Nie można usunąć pliku tymczasowego paczki.");
                return new Prepared(id, version, true);
            }
            String moduleId = "mod-" + hex(digest().digest(
                    ("signed:" + id).getBytes(StandardCharsets.US_ASCII))).substring(0, 24);
            unpack(payload, staging, moduleId, unpacked);
            if (!payload.delete()) throw new IOException("Nie można usunąć pliku tymczasowego paczki.");
            return new Prepared(moduleId, version, false);
        } catch (JSONException | IllegalArgumentException error) {
            throw new IOException("Nieprawidłowe metadane podpisanej paczki.", error);
        }
    }

    private static void unpack(File payload, File staging, String id, long expected)
            throws IOException, JSONException {
        ArrayList<String> assets = new ArrayList<>();
        Set<String> names = new HashSet<>();
        long total = 0;
        try (ZipFile archive = new ZipFile(payload)) {
            if (archive.size() > 4097) throw new IOException("Za dużo plików podpisanej paczki.");
            Enumeration<? extends ZipEntry> entries = archive.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                long size = entry.getSize();
                if (!names.add(name) || (!name.equals("module.json") && !name.matches(ASSET))
                        || size < 0 || size > ZIP_LIMIT || size > Math.max(1, entry.getCompressedSize()) * 100
                        || (total += size) > expected)
                    throw new IOException("Nieprawidłowy plik lub rozmiar podpisanej paczki.");
                if (!name.equals("module.json")) assets.add(name);
            }
            if (total != expected || !names.contains("module.json"))
                throw new IOException("Niekompletna podpisana paczka.");
            JSONObject recipe;
            ZipEntry recipeEntry = archive.getEntry("module.json");
            try (CheckedInputStream input = new CheckedInputStream(archive.getInputStream(recipeEntry), new CRC32())) {
                byte[] data = read(input, META_LIMIT);
                if (data.length != recipeEntry.getSize() || input.getChecksum().getValue() != recipeEntry.getCrc())
                    throw new IOException("Nieprawidłowa suma kontrolna deklaracji modułu.");
                recipe = new JSONObject(new String(data, StandardCharsets.UTF_8));
            }
            String source = recipe.getString("source");
            String stage = recipe.getString("stage");
            if (recipe.length() != 2 || !assets.contains(source) || !source.endsWith(".txt")
                    || !assets.contains(stage) || !stage.endsWith(".dat"))
                throw new IOException("Nieprawidłowa deklaracja modułu.");
            if (!new File(staging, "assets/a").mkdirs())
                throw new IOException("Nie można przygotować katalogu zasobów.");
            Collections.sort(assets);
            for (String name : assets) {
                ZipEntry entry = archive.getEntry(name);
                if (staging.getFreeSpace() < entry.getSize() + RESERVE)
                    throw new IOException("Za mało miejsca na zasoby modułu.");
                try (CheckedInputStream input = new CheckedInputStream(archive.getInputStream(entry), new CRC32());
                     FileOutputStream output = new FileOutputStream(new File(staging, name))) {
                    if (copy(input, output, entry.getSize(), null) != entry.getSize()
                            || input.getChecksum().getValue() != entry.getCrc())
                        throw new IOException("Nieprawidłowy rozmiar zasobu.");
                }
            }
            String prefix = "mods/" + id + "/";
            StringBuilder manifest = new StringBuilder("id=").append(id)
                    .append("\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n")
                    .append("extend=base/game/catalog|catalog.lua\nextend=base/game/sounds|sounds.lua\n");
            for (String name : assets)
                manifest.append("asset=").append(prefix).append(name.substring(7)).append('|').append(name).append('\n');
            write(staging, "package.manifest", manifest.toString());
            write(staging, "catalog.lua", "return function(base)\n base.source_path=\"" + prefix
                    + source.substring(7) + "\"\n base.stage_path=\"" + prefix + stage.substring(7)
                    + "\"\n base.profile_id=\"" + id + "\"\n return base\nend\n");
            write(staging, "sounds.lua", "return function(base)\n local paths={\n }\n"
                    + " for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end\n"
                    + " for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end\n return base\nend\n");
        }
    }

    /** Unpacks a signed full content pack (its Lua is trusted through the publisher signature). */
    private static void unpackContentPack(File payload, File staging, String id, long expected,
            Progress progress) throws IOException {
        String root = staging.getCanonicalPath() + File.separator;
        Set<String> names = new HashSet<>();
        long total = 0;
        try (ZipFile archive = new ZipFile(payload)) {
            ArrayList<ZipEntry> files = new ArrayList<>();
            Enumeration<? extends ZipEntry> entries = archive.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry.isDirectory()) continue;
                String name = entry.getName();
                String lower = name.toLowerCase(java.util.Locale.ROOT);
                if (files.size() >= PACK_FILES || !safePath(name) || lower.matches(FORBIDDEN)
                        || !names.add(lower) || entry.getSize() < 0 || (total += entry.getSize()) > expected)
                    throw new IOException("Nieprawidłowy plik w paczce modułu: " + name);
                files.add(entry);
            }
            if (total != expected || !names.contains("package.manifest"))
                throw new IOException("Niekompletna paczka modułu.");
            int done = 0;
            for (ZipEntry entry : files) {
                File target = new File(staging, entry.getName()).getCanonicalFile();
                if (!target.getPath().startsWith(root)) throw new IOException("Ścieżka wychodzi poza paczkę.");
                File parent = target.getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Nie można utworzyć katalogu paczki.");
                if (staging.getFreeSpace() < entry.getSize() + RESERVE)
                    throw new IOException("Za mało miejsca na zasoby modułu.");
                try (CheckedInputStream input = new CheckedInputStream(archive.getInputStream(entry), new CRC32());
                     FileOutputStream output = new FileOutputStream(target)) {
                    if (copy(input, output, entry.getSize(), null) != entry.getSize()
                            || input.getChecksum().getValue() != entry.getCrc())
                        throw new IOException("Uszkodzony plik paczki: " + entry.getName());
                }
                if (progress != null && (++done % 50 == 0 || done == files.size())) progress.update(done, files.size());
            }
        }
        String manifest;
        try (InputStream input = new java.io.FileInputStream(new File(staging, "package.manifest"))) {
            manifest = new String(read(input, META_LIMIT), StandardCharsets.UTF_8);
        }
        boolean declared = false;
        for (String line : manifest.split("\\r?\\n")) declared |= line.equals("id=" + id);
        if (!declared) throw new IOException("package.manifest opisuje inny moduł.");
    }

    private static boolean safePath(String name) {
        if (name.isEmpty() || name.length() > 240 || name.startsWith("/") || name.indexOf('\\') >= 0
                || name.indexOf(':') >= 0 || name.indexOf('\0') >= 0) return false;
        for (String part : name.split("/", -1))
            if (part.isEmpty() || part.equals(".") || part.equals("..")) return false;
        return true;
    }

    private static JSONObject signed(byte[] raw, byte[] signature, byte[] key)
            throws IOException, JSONException {
        if (key == null || key.length != 32) throw new IOException("Brak zaufanego klucza katalogu modów.");
        Ed25519Signer verifier = new Ed25519Signer();
        verifier.init(false, new Ed25519PublicKeyParameters(key, 0));
        verifier.update(raw, 0, raw.length);
        if (signature.length != 64 || !verifier.verifySignature(signature))
            throw new IOException("Nieprawidłowy podpis katalogu lub manifestu.");
        return new JSONObject(new String(raw, StandardCharsets.UTF_8));
    }

    private static boolean atLeast(String current, String minimum) {
        if (!minimum.matches("(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)")) return false;
        String[] left = current.split("\\.");
        String[] right = minimum.split("\\.");
        for (int i = 0; i < 3; i++) {
            int difference = new BigInteger(left[i]).compareTo(new BigInteger(right[i]));
            if (difference != 0) return difference > 0;
        }
        return true;
    }

    private static void expect(ZipInputStream stream, String name) throws IOException {
        ZipEntry entry = stream.getNextEntry();
        if (entry == null || !name.equals(entry.getName())) throw new IOException("Niekompletna podpisana paczka.");
    }

    static byte[] read(InputStream input, long limit) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        copy(input, output, limit, null);
        return output.toByteArray();
    }

    private static long copy(InputStream input, java.io.OutputStream output, long limit,
                             MessageDigest hash) throws IOException {
        byte[] buffer = new byte[65536];
        long size = 0;
        int read;
        while ((read = input.read(buffer)) != -1) {
            size += read;
            if (size > limit) throw new IOException("Paczka przekracza zadeklarowany rozmiar.");
            output.write(buffer, 0, read);
            if (hash != null) hash.update(buffer, 0, read);
        }
        return size;
    }

    private static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            result.append(Character.forDigit((b & 255) >>> 4, 16));
            result.append(Character.forDigit(b & 15, 16));
        }
        return result.toString();
    }

    private static void write(File directory, String name, String text) throws IOException {
        try (FileOutputStream output = new FileOutputStream(new File(directory, name))) {
            output.write(text.getBytes(StandardCharsets.UTF_8));
        }
    }
}
