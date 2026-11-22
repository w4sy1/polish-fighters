package io.github.openlf2.openlf2;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** LF2-styled source browser and file-picker importer for converted packages. */
public final class AndroidModsActivity extends Activity {
    static final String FROM_RUNNING_GAME="from_running_game";
    static final String SELECTED_PROFILE="selected_profile";
    static final String ACTIVE_PACKAGE="active_package";
    static final String FIRST_SETUP="first_setup";
    private static final int PICK_PACKAGE=7301;
    private static final int NAVY=0xff101f6c, BLUE=0xff81baf0, TEXT=0xfff4f5ff, MUTED=0xffc6d5f4, GOLD=0xffffdc82;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout rows;
    private ScrollView scroll;
    private Runnable previousScreen;
    private TextView title, status;
    private ProgressBar progress;
    private ClassicButton prefetchAction;
    private boolean importing;
    private boolean fetchingCatalogue;
    private final int[] baseChoices = {1, 2, 0};
    private final boolean[] setupSelection = new boolean[GamePackSettings.IDS.length];
    private int setupBase = 1;
    private List<AndroidModSources.Package> setupCatalogue = java.util.Collections.emptyList();
    private int queueIndex, queueTotal;

    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(NAVY);
        ImageView art = new ImageView(this);
        art.setImageResource(R.drawable.pf_loading_art_landscape);
        art.setScaleType(ImageView.ScaleType.CENTER_CROP);
        art.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        root.addView(art, new FrameLayout.LayoutParams(-1, -1));
        View tint = new View(this);
        tint.setBackground(new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,
            new int[]{0xc0101f6c, 0xee101f6c, NAVY}));
        root.addView(tint, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout screen = new LinearLayout(this);
        screen.setGravity(Gravity.CENTER_HORIZONTAL);
        root.addView(screen, new FrameLayout.LayoutParams(-1, -1));
        screen.setPadding(dp(12), dp(6), dp(12), dp(4));
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            screen.setPadding(insets.getSystemWindowInsetLeft() + dp(12),
                insets.getSystemWindowInsetTop() + dp(6),
                insets.getSystemWindowInsetRight() + dp(12),
                insets.getSystemWindowInsetBottom() + dp(4));
            return insets;
        });

        LinearLayout menu = new LinearLayout(this);
        menu.setOrientation(LinearLayout.VERTICAL);
        menu.setGravity(Gravity.CENTER_HORIZONTAL);
        int width = Math.min(540, getResources().getConfiguration().screenWidthDp - 24);
        screen.addView(menu, new LinearLayout.LayoutParams(width > 0 ? dp(width) : -1, -1));
        title = label("KATALOG MODÓW", 20, TEXT, false);
        title.setPadding(0, dp(3), 0, dp(5));
        menu.addView(title, wrap());

        scroll = new ScrollView(this);
        scroll.setVerticalFadingEdgeEnabled(true);
        scroll.setFadingEdgeLength(dp(8));
        scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        rows = new LinearLayout(this);
        rows.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(rows);
        menu.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        status = label("", 12, GOLD, false);
        status.setMaxLines(3);
        status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        menu.addView(status, wrap());
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        progress.setVisibility(View.GONE);
        progress.setProgressTintList(android.content.res.ColorStateList.valueOf(GOLD));
        menu.addView(progress, new LinearLayout.LayoutParams(-1, dp(6)));

        prefetchAction = action("", this::runPrefetchQueue);
        prefetchAction.setActivated(true);
        prefetchAction.setVisibility(View.GONE);
        menu.addView(prefetchAction, wrap());
        LinearLayout footer = new LinearLayout(this);
        footer.addView(action("IMPORTUJ ZIP", this::pickPackage), new LinearLayout.LayoutParams(0, -2, 1));
        footer.addView(action("WSTECZ", this::goBack), new LinearLayout.LayoutParams(0, -2, 1));
        menu.addView(footer, wrap());
        setContentView(root);
        if (getIntent().getBooleanExtra(FIRST_SETUP,false)) showSetup();
        else if (fromGame()) showGitHub();
        else showSources();
    }

    private LinearLayout.LayoutParams wrap() { return new LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT); }
    private TextView label(String value,int size,int color,boolean bold) {
        TextView view=new TextView(this);view.setText(value);view.setTextColor(color);view.setTextSize(size);
        view.setTypeface(Typeface.SANS_SERIF,bold?Typeface.BOLD:Typeface.NORMAL);view.setGravity(Gravity.CENTER);return view;
    }
    private ClassicButton action(String label,Runnable click) {
        // The pixel font has no dashes or ellipsis; they would be drawn as "?".
        ClassicButton button=new ClassicButton(this);button.setText(label.replace("—","-").replace("–","-").replace("…","..."));button.setContentDescription(label);button.setAllCaps(false);button.setMinHeight(dp(44));button.setMenuRowStyle();button.setOnClickListener(v->click.run());return button;
    }
    private int dp(int value) { return Math.round(value*getResources().getDisplayMetrics().density); }

    private void showSources() {
        title.setText("KATALOG MODÓW");
        previousScreen = null;
        scroll.scrollTo(0,0);
        rows.removeAllViews();
        prefetchAction.setVisibility(View.GONE);
        ClassicButton github=action("POBIERZ: "+AndroidModSources.GITHUB_NAME,this::showGitHub);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(github,params);
        rows.addView(action("KONFIGURACJA GRY",this::openSetup),wrap());
        status.setText("Otwórz katalog Polish Fighters albo zaimportuj lokalną paczkę ZIP.");
    }
    private void openSetup() {
        if (importing) return;
        try {
            GamePackSettings settings = new GamePackSettings(getFilesDir());
            String mode = settings.mode();
            if (GamePackSettings.CUSTOM.equals(mode) || GamePackSettings.ALL.equals(mode)) {
                boolean[] saved = settings.selection();
                System.arraycopy(saved,0,setupSelection,0,saved.length);
                for (int index : baseChoices) {
                    if (setupSelection[index]) { setupBase=index; break; }
                }
            } else {
                java.util.Arrays.fill(setupSelection,false);
                setupBase=1;
                for (int index : baseChoices) if (GamePackSettings.IDS[index].equals(mode)) setupBase=index;
                for (int index=3;index<setupSelection.length;index++) {
                    if (GamePackSettings.IDS[index].equals(mode)) setupSelection[index]=true;
                }
            }
            showSetup();
        } catch (Exception error) { setBusy(false,"Nie można odczytać konfiguracji: "+safe(error.getMessage())); }
    }
    private void showSetup() {
        previousScreen = getIntent().getBooleanExtra(FIRST_SETUP,false) ? null : this::showSources;
        rows.removeAllViews();
        prefetchAction.setVisibility(View.GONE);
        scroll.scrollTo(0,0);
        title.setText("KONFIGURACJA GRY");
        if (getIntent().getBooleanExtra(FIRST_SETUP,false)) {
            rows.addView(action("POMIŃ POBIERANIE - GRAJ OD RAZU",this::skipSetupDownloads),wrap());
        }
        for (int index : baseChoices) {
            ClassicButton row = action((setupBase==index ? "[X] " : "[ ] ")+GamePackSettings.TITLES[index],()->{
                if (importing) return;
                int offset=scroll.getScrollY();
                setupBase=index;showSetup();restoreScroll(offset);
            });
            row.setActivated(setupBase == index);
            rows.addView(row,wrap());
        }
        rows.addView(label("DODATKI DO WSPÓLNEJ PULI",14,TEXT,true),wrap());
        for (int i=3;i<setupSelection.length;i++) {
            final int index=i;
            ClassicButton row = action((setupSelection[index] ? "[X] " : "[ ] ")+GamePackSettings.TITLES[index],()->{
                if (importing) return;
                int offset=scroll.getScrollY();
                setupSelection[index]=!setupSelection[index];showSetup();restoreScroll(offset);
            });
            row.setActivated(setupSelection[index]);
            rows.addView(row,wrap());
        }
        boolean mixed=usesMixedPool();
        GamePackSettings settings = new GamePackSettings(getFilesDir());
        List<String> missing = missingSetupPacks(settings,mixed);
        rows.addView(label(mixed ? "Wymagane paczki: Polish Fighters i Wszystkie razem. Wspólna pula jest przeznaczona do gry lokalnej."
                : "Wymagany jest wybrany moduł bazowy.",12,MUTED,false),wrap());
        if (missing.isEmpty()) {
            rows.addView(action("ZAPISZ I URUCHOM GRĘ",()->saveSetup(mixed)),wrap());
            setBusy(false,!mixed && setupBase==1
                    ? "Gra użyje lokalnych danych LF2 lub poprosi o ich przygotowanie."
                    : "Wybrane paczki są dostępne lokalnie.");
            addPrefetchSection();
            return;
        }
        List<AndroidModSources.Package> download = new java.util.ArrayList<>();
        long bytes=0, required=0;
        for (String id : missing) {
            for (AndroidModSources.Package item : setupCatalogue) {
                if (!id.equals(item.id)) continue;
                download.add(item);bytes+=item.size;required+=item.unpacked;
                break;
            }
        }
        if (download.size()!=missing.size()) {
            rows.addView(action("SPRAWDŹ KATALOG GITHUB",this::loadSetupCatalogue),wrap());
            setBusy(false,"Brakujące paczki: "+android.text.TextUtils.join(", ",missing)+". Sprawdź katalog, aby poznać ich rozmiar.");
        } else {
            required+=2*bytes+64L*1024*1024;
            rows.addView(label("Pobieranie: "+formatMiB(bytes)+" · wymagane wolne miejsce: "+formatMiB(required),13,TEXT,false),wrap());
            final long freeRequired=required;
            rows.addView(action("POBIERZ I URUCHOM GRĘ",()->downloadSetup(download,mixed,freeRequired)),wrap());
            setBusy(false,"Brakujące paczki: "+android.text.TextUtils.join(", ",missing)+".");
        }
        addPrefetchSection();
    }
    // Punkt 4: multi-select batch download. Independent of the base-pack/mixed-pool logic
    // above - this just lets the first-run screen fetch several catalogue packages in one
    // confirmation, with per-item progress, so the player can pick between them later in the
    // normal single-profile selector instead of waiting through one download at a time.
    private void addPrefetchSection() {
        rows.addView(label("POBIERZ NA ZAPAS",14,TEXT,true),wrap());
        if (setupCatalogue.isEmpty()) {
            rows.addView(action("SPRAWDŹ KATALOG, ABY WYBRAĆ KILKA PACZEK",this::loadSetupCatalogue),wrap());
            return;
        }
        java.util.Set<String> queued;
        try { queued = new GamePackSettings(getFilesDir()).prefetchQueue(); }
        catch (Exception error) { queued = java.util.Collections.emptySet(); }
        int pending = 0;
        for (AndroidModSources.Package item : setupCatalogue) {
            boolean installed = item.receipt().equals(installedReceipt(item));
            boolean checked = queued.contains(item.id);
            if (checked && !installed) pending++;
            final String id = item.id;
            String mark = installed ? "[OK] " : checked ? "[X] " : "[ ] ";
            ClassicButton row = action(mark+item.name+" "+item.version+" - "+item.sizeLabel(),()->{
                if (importing) return;
                toggleQueued(id);
            });
            row.setActivated(checked || installed);
            rows.addView(row,wrap());
        }
        if (pending > 0) {
            prefetchAction.setText("POBIERZ ZAZNACZONE PACZKI ["+pending+"]");
            prefetchAction.setContentDescription(prefetchAction.getText());
            prefetchAction.setVisibility(View.VISIBLE);
        }
    }
    private void toggleQueued(String id) {
        int offset = scroll.getScrollY();
        try {
            GamePackSettings settings = new GamePackSettings(getFilesDir());
            java.util.LinkedHashSet<String> next = new java.util.LinkedHashSet<>(settings.prefetchQueue());
            if (!next.remove(id)) next.add(id);
            settings.savePrefetchQueue(next);
        } catch (Exception error) { setBusy(false,"Nie można zapisać wyboru: "+safe(error.getMessage()));return; }
        showSetup();
        restoreScroll(offset);
    }
    private void skipSetupDownloads() {
        if (importing) return;
        setupBase = 1; // LF2 Classic - no content pack required, nothing to download.
        java.util.Arrays.fill(setupSelection,false);
        saveSetup(false);
    }
    /**
     * Downloads+installs every queued-but-not-yet-installed catalogue entry, one at a time,
     * reporting "item i of n". The queue itself is already persisted (toggleQueued), so if the
     * process dies or the network drops mid-batch, reopening setup and pressing this again
     * naturally skips whatever already matches its installed receipt - no separate resume state.
     */
    private void runPrefetchQueue() {
        if (importing) return;
        GamePackSettings settings = new GamePackSettings(getFilesDir());
        java.util.Set<String> queued;
        try { queued = settings.prefetchQueue(); }
        catch (Exception error) { setBusy(false,"Nie można odczytać listy pobierań: "+safe(error.getMessage())); return; }
        List<AndroidModSources.Package> pending = new java.util.ArrayList<>();
        for (AndroidModSources.Package item : setupCatalogue)
            if (queued.contains(item.id) && !item.receipt().equals(installedReceipt(item))) pending.add(item);
        if (pending.isEmpty()) { showSetup(); return; }
        long bytes = 0; for (AndroidModSources.Package item : pending) bytes += item.size;
        long required = 2*bytes + 64L*1024*1024;
        if (getFilesDir().getFreeSpace() < required) { setBusy(false,"Za mało wolnego miejsca: "+formatMiB(required)); return; }
        cancellationRequested = false;
        downloading = true;
        queueTotal = pending.size(); queueIndex = 0;
        setBusy(true,"Przygotowuję pobieranie "+queueTotal+" paczek…");
        worker.submit(() -> {
            for (AndroidModSources.Package item : pending) {
                if (cancellationRequested) break;
                queueIndex++;
                final int current = queueIndex, total = queueTotal;
                final String name = item.name;
                runOnUiThread(() -> status.setText("Pozycja "+current+" z "+total+": "+name));
                try {
                    transferAndInstall(item);
                } catch (Exception error) {
                    downloading = false;
                    android.util.Log.w("OpenLF2","Prefetch queue item failed: "+item.id,error);
                    boolean cancelled = cancellationRequested;
                    runOnUiThread(() -> {
                        showSetup();
                        setBusy(false, cancelled
                            ? "Pobieranie wstrzymane. Zaznaczone pozycje czekają - wybierz \"POBIERZ ZAZNACZONE PACZKI\" ponownie, aby wznowić."
                            : "Nie udało się pobrać "+name+": "+safe(error.getMessage())+". Pozostałe pozycje czekają w kolejce.");
                    });
                    return;
                }
            }
            downloading = false;
            runOnUiThread(() -> { showSetup(); setBusy(false,"Pobrano zaznaczone paczki."); });
        });
    }
    private boolean usesMixedPool() {
        for (int i=3;i<setupSelection.length;i++) if (setupSelection[i]) return true;
        return false;
    }
    private List<String> missingSetupPacks(GamePackSettings settings,boolean mixed) {
        List<String> missing = new java.util.ArrayList<>();
        if (mixed) {
            for (String id : new String[]{"polish-originals","mixed-all"}) if (!settings.hasPack(id)) missing.add(id);
        } else {
            String id=GamePackSettings.PACKS[setupBase];
            if (!id.isEmpty() && !settings.hasPack(id)) missing.add(id);
        }
        return missing;
    }
    private String formatMiB(long size) { return String.format(java.util.Locale.getDefault(),"%.1f MiB",size/1048576.0); }
    private void loadSetupCatalogue() {
        if (importing) return;
        setBusy(true,"Pobieram podpisany katalog…");
        worker.submit(()->{
            try {
                List<AndroidModSources.Package> found=AndroidModSources.fetchGitHubCatalogue(trustedKey());
                runOnUiThread(()->{ setupCatalogue=found;showSetup(); });
            } catch (Exception error) {
                runOnUiThread(()->setBusy(false,"Nie można pobrać katalogu: "+safe(error.getMessage())));
            }
        });
    }
    private void downloadSetup(List<AndroidModSources.Package> items,boolean mixed,long required) {
        if (importing) return;
        if (getFilesDir().getFreeSpace()<required) { setBusy(false,"Za mało wolnego miejsca: "+formatMiB(required));return; }
        cancellationRequested=false;
        downloading=true;
        setBusy(true,"Przygotowuję pobieranie…");
        worker.submit(()->{
            try {
                for (AndroidModSources.Package item : items) transferAndInstall(item);
                runOnUiThread(()->{ setBusy(false,"Paczki są gotowe.");saveSetup(mixed); });
            } catch (Exception error) {
                runOnUiThread(()->{ showSetup();setBusy(false,"Instalacja przerwana: "+safe(error.getMessage())); });
            }
        });
    }
    private void saveSetup(boolean mixed) {
        if (importing) return;
        try {
            GamePackSettings settings = new GamePackSettings(getFilesDir());
            if (!missingSetupPacks(settings,mixed).isEmpty()) throw new java.io.IOException("Brak wymaganych danych.");
            boolean[] selected=setupSelection.clone();
            for (int index : baseChoices) selected[index]=index==setupBase;
            settings.save(mixed ? GamePackSettings.CUSTOM : GamePackSettings.IDS[setupBase],selected,settings.hideDuplicates());
            startActivity(new Intent(this,OpenLF2Activity.class));
            finish();
        } catch (Exception error) { setBusy(false,"Nie zapisano konfiguracji: "+safe(error.getMessage())); }
    }
    private byte[] trustedKey() throws java.io.IOException {
        try(java.io.InputStream key=getAssets().open(SignedModPackage.KEY_ASSET)){return SignedModPackage.read(key,32);}
    }
    private void showGitHub() {
        if (importing) return;
        fetchingCatalogue=true;
        setBusy(true,"Pobieram podpisany katalog: "+AndroidModSources.GITHUB_NAME);
        worker.submit(()->{
            try {
                List<AndroidModSources.Package> found=AndroidModSources.fetchGitHubCatalogue(trustedKey());
                runOnUiThread(()->{
                    if (isFinishing() || isDestroyed()) return;
                    fetchingCatalogue=false;
                    showPackages(found,scroll.getScrollY(),scroll.getScrollY());
                });
            }
            catch(Exception error) { runOnUiThread(()->{
                if (isFinishing() || isDestroyed()) return;
                fetchingCatalogue=false;
                if (rows.getChildCount()==0) {
                    if (fromGame()) showPackages(java.util.Collections.emptyList(),0,0);
                    else showSources();
                }
                setBusy(false,"Nie udało się pobrać katalogu. "+safe(error.getMessage()));
            }); }
        });
    }
    private boolean fromGame() {
        return getIntent().getBooleanExtra(FROM_RUNNING_GAME, false);
    }

    private void showPackages(List<AndroidModSources.Package> found,int sourceOffset,int catalogueOffset) {
        title.setText("KATALOG MODÓW");
        previousScreen = fromGame() ? null : () -> { showSources(); restoreScroll(sourceOffset); };
        rows.removeAllViews();
        prefetchAction.setVisibility(View.GONE);
        String activePackage = getIntent().getStringExtra(ACTIVE_PACKAGE);
        if (fromGame()) {
            rows.addView(action("LF2 CLASSIC · " + ("".equals(activePackage) ? "AKTYWNY" : "WYBIERZ"),
                () -> selectProfile("lf_two", "")),wrap());
            GamePackSettings settings = new GamePackSettings(getFilesDir());
            for (int i=0; i<GamePackSettings.IDS.length; i++) {
                String id=GamePackSettings.PACKS[i], profile=GamePackSettings.IDS[i];
                if (id.isEmpty() || containsPackage(found,id) || !settings.hasPack(id)) continue;
                String operation=id.equals(activePackage) ? "AKTYWNY" : "WYBIERZ";
                rows.addView(action(GamePackSettings.TITLES[i]+" · "+operation, () -> selectProfile(profile,id)),wrap());
            }
            for (String id : settings.imported()) {
                rows.addView(action("MOD " + id.substring(4,12) + " · " + (id.equals(activePackage) ? "AKTYWNY" : "WYBIERZ"),
                    () -> selectProfile(id,id)),wrap());
            }
        }
        for (AndroidModSources.Package item : found) {
            String receipt = installedReceipt(item);
            boolean current = item.receipt().equals(receipt);
            boolean active = item.id.equals(activePackage);
            String operation = receipt == null ? "POBIERZ" : !current ? "AKTUALIZUJ"
                : active ? "AKTYWNY" : item.profile.isEmpty() ? "ZAINSTALOWANO" : "WYBIERZ";
            ClassicButton button = action(item.name+" "+item.version+" · "+operation, () -> {
                if (importing) return;
                if (!current) install(item,found,sourceOffset,scroll.getScrollY());
                else if (!active && !item.profile.isEmpty()) selectProfile(item.profile,item.id);
            });
            button.setContentDescription(item.name+", "+item.version+", "+item.sizeLabel()+", "+operation);
            rows.addView(button,wrap());
        }
        rows.addView(action("ODŚWIEŻ KATALOG", this::showGitHub),wrap());
        restoreScroll(catalogueOffset);
        String activeLabel = activePackage == null ? "" : " · Aktywny: " + (activePackage.isEmpty() ? "LF2 Classic" : activePackage);
        setBusy(false,"Podpis katalogu poprawny."+activeLabel);
    }

    private static boolean containsPackage(List<AndroidModSources.Package> packages, String id) {
        for (AndroidModSources.Package item : packages) if (id.equals(item.id)) return true;
        return false;
    }

    private void selectProfile(String profile, String packageId) {
        if (importing || (fromGame() && packageId.equals(getIntent().getStringExtra(ACTIVE_PACKAGE)))) return;
        try {
            GamePackSettings settings = new GamePackSettings(getFilesDir());
            settings.save(profile,settings.selection(),settings.hideDuplicates());
            if (fromGame()) {
                setResult(RESULT_OK,new Intent().putExtra(SELECTED_PROFILE,profile));
                finish();
            } else {
                setBusy(false,"Moduł wybrany do gry.");
            }
        } catch (Exception error) {
            setBusy(false,"Nie zapisano wyboru: "+safe(error.getMessage()));
        }
    }
    private java.io.File packageFolder(AndroidModSources.Package item) {
        return new java.io.File(getFilesDir(),"game/content-packs/"+item.id);
    }
    private String installedReceipt(AndroidModSources.Package item) {
        java.io.File folder = packageFolder(item);
        if (!new java.io.File(folder,"package.manifest").isFile()) return null;
        try (java.io.InputStream input = new java.io.FileInputStream(new java.io.File(folder,".github-install"))) {
            return new String(SignedModPackage.read(input,128),java.nio.charset.StandardCharsets.US_ASCII);
        } catch (java.io.IOException error) { return ""; }
    }
    private void install(AndroidModSources.Package item,List<AndroidModSources.Package> catalogue,
            int sourceOffset,int catalogueOffset) {
        if (importing || item.receipt().equals(installedReceipt(item))) return;
        cancellationRequested=false;
        downloading=true;
        setBusy(true,"Przygotowuję pobieranie…");
        worker.submit(()->{
            try {
                transferAndInstall(item);
                downloading=false;
                runOnUiThread(()->{
                    showPackages(catalogue,sourceOffset,catalogueOffset);
                    status.setText("Zainstalowano "+item.name+" "+item.version+".");
                });
            } catch (Exception error) {
                downloading=false;
                android.util.Log.w("OpenLF2","GitHub mod install failed",error);
                runOnUiThread(()->setBusy(false,cancellationRequested
                    ? "Anulowano pobieranie." : "Instalacja przerwana: "+safe(error.getMessage())));
            }
        });
    }
    private volatile boolean downloading;
    private volatile boolean cancellationRequested;
    private void transferAndInstall(AndroidModSources.Package item) throws java.io.IOException {
        java.io.File folder=new java.io.File(getCacheDir(),"mods");
        if (!folder.isDirectory()&&!folder.mkdirs()) throw new java.io.IOException("Nie można przygotować katalogu pobierania.");
        java.io.File envelope=new java.io.File(folder,item.id+"-"+item.version+"-"+item.sha256+".zip");
        long partial=new java.io.File(envelope.getPath()+".part").length();
        long needed=2*item.size+item.unpacked+64L*1024*1024-(partial<item.size ? partial : 0);
        if (getFilesDir().getFreeSpace()<needed) throw new java.io.IOException("Za mało miejsca: "+formatMiB(needed));
        runOnUiThread(()->{
            status.setText("Pobieram "+item.name+"…");
            progress.setIndeterminate(false);progress.setMax(1000);progress.setProgress(0);
        });
        try {
            final long[] shown={-1};
            AndroidModSources.download(item,envelope,(received,total)->{
                long permille=received*1000/total;
                if (permille!=shown[0]) {
                    shown[0]=permille;
                    runOnUiThread(()->{
                        progress.setProgress((int)permille);
                        status.setText("Pobieram "+item.name+": "+formatMiB(received)+" / "+formatMiB(total)+" ("+permille/10+"%)");
                    });
                }
                return !cancellationRequested && !worker.isShutdown();
            });
            downloading=false;
            if (cancellationRequested) throw new java.io.IOException("Anulowano pobieranie.");
            runOnUiThread(()->{progress.setIndeterminate(true);status.setText("Sprawdzam podpis i instaluję "+item.name+"…");});
            String id=AndroidModPackageImporter.importDownloaded(envelope,getFilesDir(),getAssets(),item,
                    files->runOnUiThread(()->status.setText("Instaluję "+item.name+": plików "+files)));
            android.util.Log.i("OpenLF2","GitHub mod installed: "+id);
        } finally { envelope.delete(); }
    }
    private void pickPackage() {
        if (importing) return;
        Intent request=new Intent(Intent.ACTION_OPEN_DOCUMENT);request.setType("application/zip");request.addCategory(Intent.CATEGORY_OPENABLE);request.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try { startActivityForResult(request,PICK_PACKAGE); }
        catch(Exception error) { setBusy(false,"Systemowy selektor plików jest niedostępny."); }
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=PICK_PACKAGE||resultCode!=RESULT_OK||data==null||data.getData()==null)return;
        Uri selected=data.getData();setBusy(true,"Sprawdzam i importuję paczkę…");
        worker.submit(()->{
            try {
                String id=AndroidModPackageImporter.importPackage(getContentResolver(),selected,getFilesDir(),getAssets(),entries->runOnUiThread(()->status.setText("Sprawdzono plików: "+entries)));
                runOnUiThread(()->{
                    setBusy(false,"Zaimportowano "+id+".");
                    if (!fromGame()) selectProfile(id,id);
                    rows.addView(action("WYBIERZ MOD "+id.substring(4,12),()->selectProfile(id,id)),wrap());
                    scroll.post(()->scroll.fullScroll(View.FOCUS_DOWN));
                });
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Import przerwany: "+safe(error.getMessage()))); }
        });
    }
    private void leave() { finish(); }
    private void restoreScroll(int offset) { scroll.post(() -> scroll.scrollTo(0,offset)); }
    private void goBack() {
        if (importing) {
            if (fetchingCatalogue && fromGame()) { leave(); return; }
            if (downloading) {
                cancellationRequested=true;
                status.setText("Anulowanie pobierania…");
            }
            return;
        }
        if (previousScreen == null) leave();
        else previousScreen.run();
    }
    @Override public boolean onKeyUp(int keyCode, android.view.KeyEvent event) {
        if (keyCode != android.view.KeyEvent.KEYCODE_ESCAPE) return super.onKeyUp(keyCode,event);
        goBack();
        return true;
    }
    @Override public void onBackPressed() { goBack(); }
    private void setBusy(boolean busy,String message) { importing=busy;prefetchAction.setEnabled(!busy);status.setText(message);if(!busy)progress.setIndeterminate(true);progress.setVisibility(busy?View.VISIBLE:View.GONE); }
    private static String safe(String value) { if(value==null)return "nieznany błąd";String text=value.replaceAll("[\\r\\n\\p{Cntrl}]"," ");return text.substring(0,Math.min(text.length(),240)); }
    @Override protected void onDestroy() { worker.shutdownNow();super.onDestroy(); }
}
