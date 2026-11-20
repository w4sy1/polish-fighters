package io.github.openlf2.openlf2;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/** Installs a data-only package produced by the project's legacy-data converter. */
final class AndroidModPackageImporter {
    private static final int MAX_ENTRIES = 20000;
    private static final long MAX_ENTRY = 512L * 1024 * 1024;
    private static final long MAX_TOTAL = 2L * 1024 * 1024 * 1024;
    private static final Pattern ID = Pattern.compile("mod-[a-f0-9]{24}");
    private AndroidModPackageImporter() {}

    static String importPackage(ContentResolver resolver, Uri uri, File filesDirectory,
            AssetManager assets, Progress progress) throws IOException {
        InputStream raw=resolver.openInputStream(uri);
        if(raw==null) throw new IOException("Nie można odczytać wybranego pliku.");
        return importPackage(raw, filesDirectory, () -> {
            try (InputStream key = assets.open(SignedModPackage.KEY_ASSET)) {
                return SignedModPackage.read(key, 32);
            } catch (IOException error) {
                throw new IOException("Brak zaufanego klucza katalogu modów.", error);
            }
        }, BuildConfig.MOD_ENGINE_VERSION, BuildConfig.MOD_GOOGLE_PLAY, progress);
    }

    static String importPackage(InputStream raw, File filesDirectory, Progress progress) throws IOException {
        return importPackage(raw, filesDirectory, () -> null, BuildConfig.MOD_ENGINE_VERSION, false, progress);
    }

    static String importPackage(InputStream raw, File filesDirectory, KeySource key,
            String engineVersion, boolean googlePlay, Progress progress) throws IOException {
        return importPackage(raw, filesDirectory, key, engineVersion, googlePlay, null, progress);
    }

    /** Installs a signed envelope downloaded from the GitHub catalogue; it must contain `expectedId`. */
    static String importDownloaded(File envelope, File filesDirectory, AssetManager assets, String expectedId,
            Progress progress) throws IOException {
        return importPackage(new java.io.BufferedInputStream(new java.io.FileInputStream(envelope), 1 << 16),
                filesDirectory, () -> {
                    try (InputStream key = assets.open(SignedModPackage.KEY_ASSET)) { return SignedModPackage.read(key, 32); }
                    catch (IOException error) { throw new IOException("Brak zaufanego klucza katalogu modów.", error); }
                }, BuildConfig.MOD_ENGINE_VERSION, false, expectedId, progress);
    }

    static String importPackage(InputStream raw, File filesDirectory, KeySource key, String engineVersion,
            boolean googlePlay, String expectedId, Progress progress) throws IOException {
        try (ZipInputStream zip = new ZipInputStream(raw)) {
            return install(zip, filesDirectory, key, engineVersion, googlePlay, expectedId, progress);
        }
    }

    private static String install(ZipInputStream zip, File filesDirectory, KeySource key,
            String engineVersion, boolean googlePlay, String expectedId, Progress progress) throws IOException {
        File game = new File(filesDirectory, "game").getCanonicalFile();
        if (!new File(game, ".ready").isFile()) throw new IOException("Najpierw przygotuj pliki gry.");
        File packs = new File(game, "content-packs");
        if (!packs.isDirectory() && !packs.mkdirs()) throw new IOException("Nie można utworzyć katalogu modułów.");
        File staging = new File(packs, ".import-" + Long.toHexString(System.nanoTime()));
        if (!staging.mkdir()) throw new IOException("Nie można rozpocząć importu.");
        final long reserve=64L*1024*1024;
        if(staging.getFreeSpace()<reserve) { staging.delete();throw new IOException("Za mało wolnego miejsca na import."); }
        String prefix = null;
        Set<String> names = new HashSet<>();
        long total = 0;
        int count = 0;
        try {
            ZipEntry first = zip.getNextEntry();
            if (first != null && SignedModPackage.FIRST_ENTRY.equals(first.getName())) {
                SignedModPackage.Prepared prepared = SignedModPackage.prepare(zip, staging, key.load(), engineVersion,
                        expectedId, progress == null ? null : (done, all) -> progress.update(done));
                // A signed content pack carries its own Lua; trust comes from the publisher signature.
                if (prepared.contentPack) {
                    if (googlePlay) throw new IOException("Ta wersja obsługuje tylko podpisane paczki danych.");
                    return publishReplacing(staging, packs, prepared.id);
                }
                if (!prepared.id.equals(validateManifest(staging))) throw new IOException("Nieprawidłowy identyfikator modułu.");
                return publish(staging, packs, prepared.id);
            }
            if (expectedId != null) throw new IOException("Pobrany plik nie jest podpisaną paczką.");
            if (googlePlay) throw new IOException("Ta wersja obsługuje tylko podpisane paczki danych.");
                byte[] buffer = new byte[65536];
                for (ZipEntry entry = first; entry != null; entry = zip.getNextEntry()) {
                    if (++count > MAX_ENTRIES) throw new IOException("Paczka ma zbyt wiele plików.");
                    String name = entry.getName();
                    if(entry.isDirectory() && name.endsWith("/")) name=name.substring(0,name.length()-1);
                    if(entry.isDirectory() && !name.contains("/") && prefix==null) { validateName(name);prefix=name+"/";continue; }
                    validateName(name);
                    if (!names.add(name.toLowerCase(java.util.Locale.ROOT))) throw new IOException("Paczka zawiera powtórzoną ścieżkę.");
                    int slash = name.indexOf('/');
                    if (slash < 1) throw new IOException("Paczka musi zawierać jeden katalog główny.");
                    String currentPrefix = name.substring(0, slash + 1);
                    if (prefix == null) prefix = currentPrefix;
                    if (!prefix.equals(currentPrefix)) throw new IOException("Paczka zawiera kilka katalogów głównych.");
                    String relative = name.substring(prefix.length());
                    if (relative.isEmpty()) continue;
                    validateFile(relative);
                    File target = new File(staging, relative).getCanonicalFile();
                    if (!target.getPath().startsWith(staging.getCanonicalPath()+File.separator)) throw new IOException("Ścieżka wychodzi poza paczkę.");
                    if (entry.isDirectory()) {
                        if (!target.isDirectory() && !target.mkdirs()) throw new IOException("Nie można utworzyć katalogu paczki.");
                        continue;
                    }
                    File parent = target.getParentFile();
                    if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Nie można przygotować plików paczki.");
                    long written = 0;
                    try (FileOutputStream output = new FileOutputStream(target)) {
                        int n;
                        while ((n = zip.read(buffer)) != -1) {
                            written += n; total += n;
                            if (written > MAX_ENTRY || total > MAX_TOTAL) throw new IOException("Paczka przekracza limit rozmiaru.");
                            if(staging.getFreeSpace()<reserve+n) throw new IOException("Brak miejsca; import został anulowany.");
                            output.write(buffer, 0, n);
                        }
                    }
                    if (progress != null && count % 50 == 0) progress.update(count);
                }
        } catch (IOException | RuntimeException error) {
            deleteTree(staging);
            throw error;
        }
        try {
            if (prefix == null) throw new IOException("Wybrany plik nie jest paczką ZIP.");
            String id = validateManifest(staging);
            return publish(staging, packs, id);
        } catch (IOException error) {
            deleteTree(staging);
            throw error;
        }
    }

    /** Installs or updates a signed content pack in place of an older copy of the same ID. */
    private static synchronized String publishReplacing(File staging, File packs, String id) throws IOException {
        // `id` passed the manifest ID pattern, so it is one plain directory name under packs.
        File destination = new File(packs, id);
        File previous = null;
        if (destination.exists()) {
            previous = new File(packs, ".previous-" + id + "-" + Long.toHexString(System.nanoTime()));
            if (!destination.renameTo(previous)) { deleteTree(staging); throw new IOException("Nie można zastąpić starszej wersji modułu."); }
        }
        if (!staging.renameTo(destination)) {
            if (previous != null) previous.renameTo(destination);
            deleteTree(staging);
            throw new IOException("Nie można bezpiecznie zatwierdzić importu.");
        }
        if (previous != null) deleteTree(previous);
        return id;
    }

    private static synchronized String publish(File staging, File packs, String id) throws IOException {
        File destination = new File(packs, id);
        if (destination.exists() || !destination.getCanonicalFile().equals(destination))
            throw new IOException("Ten moduł jest już zaimportowany lub ścieżka jest zajęta.");
        if (!staging.renameTo(destination)) throw new IOException("Nie można bezpiecznie zatwierdzić importu.");
        return id;
    }

    private static void validateName(String name) throws IOException {
        if (name == null || name.isEmpty() || name.startsWith("/") || name.indexOf('\\') >= 0 || name.indexOf(':') >= 0)
            throw new IOException("Niebezpieczna ścieżka w paczce.");
        for (String part : name.split("/", -1)) if (part.isEmpty() || part.equals(".") || part.equals(".."))
            throw new IOException("Niebezpieczna ścieżka w paczce.");
    }

    private static void validateFile(String path) throws IOException {
        String lower = path.toLowerCase(java.util.Locale.ROOT);
        if (lower.endsWith(".exe") || lower.endsWith(".dll") || lower.endsWith(".so") || lower.endsWith(".bat")
                || lower.endsWith(".cmd") || lower.endsWith(".sh") || lower.endsWith(".py"))
            throw new IOException("Paczka zawiera plik wykonywalny lub skrypt spoza obsługiwanego formatu.");
        if (lower.endsWith(".lua") && !(path.equals("catalog.lua") || path.equals("sounds.lua")))
            throw new IOException("Paczka zawiera nieobsługiwany skrypt Lua.");
        if (!(path.equals("package.manifest") || path.equals("catalog.lua") || path.equals("sounds.lua")
                || path.equals("import-report.json") || path.equals("sprite-edge-repairs.json") || path.startsWith("assets/")))
            throw new IOException("Paczka zawiera nieobsługiwany plik: " + path);
    }

    private static String validateManifest(File root) throws IOException {
        File file = new File(root, "package.manifest");
        if (!file.isFile() || file.length() > 262144) throw new IOException("Brak poprawnego manifestu paczki.");
        String manifest = readBounded(file,262144);
        String id = null;
        Set<String> required = new HashSet<>();
        Set<String> assets = new HashSet<>();
        for (String line : manifest.split("\\r?\\n")) {
            if (line.startsWith("id=")) id = line.substring(3);
            else if (line.equals("version=1") || line.equals("api=1") || line.equals("requires=base@1")
                    || line.equals("requires=polish-fighters@1")
                    || line.equals("extend=base/game/catalog|catalog.lua")
                    || line.equals("extend=base/game/sounds|sounds.lua")) required.add(line);
            else if (line.startsWith("asset=")) {
                String value = line.substring(6); int split = value.indexOf('|');
                if (split < 1 || split == value.length() - 1) throw new IOException("Nieprawidłowy wpis zasobu.");
                String virtual = value.substring(0, split), local = value.substring(split + 1);
                validateName(virtual); validateName(local);
                if (!virtual.startsWith("mods/" + id + "/") || !local.startsWith("assets/"))
                    throw new IOException("Zasób wychodzi poza przestrzeń modułu.");
                if (!assets.add(local)) throw new IOException("Powtórzony zasób w manifeście.");
            } else if (!line.isEmpty()) throw new IOException("Manifest zawiera nieobsługiwane pole.");
        }
        if (id == null || !ID.matcher(id).matches() || required.size() != 6 || assets.isEmpty() || assets.size()>4096)
            throw new IOException("Paczka nie pochodzi z obsługiwanego konwertera.");
        for (String local : assets) if (!new File(root, local).isFile()) throw new IOException("Brak zasobu: " + local);
        if (!new File(root, "catalog.lua").isFile() || !new File(root, "sounds.lua").isFile())
            throw new IOException("Brak metadanych katalogu postaci.");
        // These converter-owned adapters are intentionally tiny; reject other Lua capabilities.
        String catalog = readBounded(new File(root, "catalog.lua"), 256 * 1024);
        String sounds = readBounded(new File(root, "sounds.lua"), 256 * 1024);
        validateCatalogScript(catalog,id,assets);
        validateSoundsScript(sounds,id);
        return id;
    }

    private static void validateCatalogScript(String script,String id,Set<String> assets) throws IOException {
        String[] lines=script.split("\\r?\\n");
        if(lines.length<6||!lines[0].equals("return function(base)")||!lines[lines.length-2].equals(" return base")||!lines[lines.length-1].equals("end"))
            throw new IOException("Nieprawidłowy adapter katalogu.");
        Pattern assignment=Pattern.compile(" base\\.(source_path|stage_path)=\"([^\"\\\\]+)\"");
        for(int i=1;i<=2;i++) {
            Matcher match=assignment.matcher(lines[i]);
            if(!match.matches()||!match.group(2).startsWith("mods/"+id+"/")||!assets.contains(match.group(2).replace("mods/"+id+"/","assets/")))
                throw new IOException("Adapter wskazuje zasób spoza paczki.");
        }
        if(!lines[3].equals(" base.profile_id=\""+id+"\"")) throw new IOException("Nieprawidłowy identyfikator profilu paczki.");
        boolean campaigns=false;
        for(int i=4;i<lines.length-2;i++) {
            String line=lines[i];
            if(line.equals(" base.campaigns={")||line.equals(" }")||line.isEmpty()) { campaigns=true;continue; }
            if(!campaigns||!line.matches(" \\{id=[0-9]{1,8},name=\"[^\"\\\\]{1,120}\",path=\"mods/"+Pattern.quote(id)+"/a/[a-z0-9]+\\.dat\",start_id=[0-9]{1,8}(,background=[0-9]{1,8})?,requires_custom_unlock=(true|false)\\},"))
                throw new IOException("Adapter zawiera nieobsługiwany kod.");
        }
    }

    private static void validateSoundsScript(String script,String id) throws IOException {
        String[] lines=script.split("\\r?\\n");
        if(lines.length<7||!lines[0].equals("return function(base)")||!lines[1].equals(" local paths={")
                ||!lines[lines.length-4].equals(" for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end")
                ||!lines[lines.length-3].equals(" for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end")
                ||!lines[lines.length-2].equals(" return base")||!lines[lines.length-1].equals("end"))
            throw new IOException("Nieprawidłowy adapter dźwięków.");
        Pattern entry=Pattern.compile(" \\[\"([a-z0-9_./-]+)\"\\]=\"mods/"+Pattern.quote(id)+"/a/[a-z0-9]+\\.wav\",");
        for(int i=2;i<lines.length-5;i++) if(!entry.matcher(lines[i]).matches()) throw new IOException("Adapter zawiera nieobsługiwany kod.");
        if(!lines[lines.length-5].equals(" }")) throw new IOException("Nieprawidłowa lista dźwięków.");
    }

    private static String readBounded(File file, int limit) throws IOException {
        if (!file.isFile() || file.length() > limit) throw new IOException("Metadane paczki są za duże.");
        try(java.io.FileInputStream input=new java.io.FileInputStream(file);java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1)output.write(buffer,0,n);
            return new String(output.toByteArray(),StandardCharsets.UTF_8);
        }
    }

    private static void deleteTree(File file) {
        File[] children = file.listFiles();
        if (children != null) for (File child : children) deleteTree(child);
        file.delete();
    }

    interface KeySource { byte[] load() throws IOException; }

    interface Progress { void update(int entries); }
}
