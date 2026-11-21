package io.github.openlf2.openlf2;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
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
    static final String FIRST_SETUP="first_setup";
    private static final int PICK_PACKAGE=7301;
    private static final int NAVY=0xff040a41, BLUE=0xff7a9dff, RED=0xffff5262, TEXT=0xfff4f5ff, MUTED=0xffb6c5d9;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout rows;
    private ScrollView scroll;
    private Runnable previousScreen;
    private TextView status;
    private ProgressBar progress;
    private boolean importing;
    private final int[] baseChoices = {1, 2, 0};
    private final boolean[] setupSelection = new boolean[GamePackSettings.IDS.length];
    private int setupBase = 1;
    private List<AndroidModSources.Package> setupCatalogue = java.util.Collections.emptyList();

    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        // Same look as the start screen: the game art, darkened towards the text, with rounded cards.
        FrameLayout root=new FrameLayout(this);root.setBackgroundColor(NAVY);
        ImageView art=new ImageView(this);art.setImageResource(R.drawable.pf_loading_art_landscape);art.setScaleType(ImageView.ScaleType.CENTER_CROP);
        art.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);root.addView(art,new FrameLayout.LayoutParams(-1,-1));
        View scrim=new View(this);scrim.setBackground(new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{0xf5040a41,0xd9040a41,0x99040a41}));
        root.addView(scrim,new FrameLayout.LayoutParams(-1,-1));

        LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.HORIZONTAL);root.addView(page,new FrameLayout.LayoutParams(-1,-1));
        // Keep the title and buttons clear of the status bar, the camera cut-out and the navigation bar.
        root.setOnApplyWindowInsetsListener((view,insets)->{
            page.setPadding(insets.getSystemWindowInsetLeft()+dp(20),insets.getSystemWindowInsetTop()+dp(14),
                insets.getSystemWindowInsetRight()+dp(20),insets.getSystemWindowInsetBottom()+dp(12));
            return insets;
        });
        page.setPadding(dp(20),dp(14),dp(20),dp(12));

        LinearLayout side=new LinearLayout(this);side.setOrientation(LinearLayout.VERTICAL);
        page.addView(side,new LinearLayout.LayoutParams(0,-1,0.92f));
        TextView kicker=label("POLISH FIGHTERS",11,RED,true);side.addView(kicker,wrap());
        TextView title=label("MODY I MODUŁY",24,TEXT,true);side.addView(title,wrap());
        View rule=new View(this);rule.setBackgroundColor(RED);LinearLayout.LayoutParams ruleParams=new LinearLayout.LayoutParams(dp(56),dp(3));ruleParams.topMargin=dp(6);ruleParams.bottomMargin=dp(10);side.addView(rule,ruleParams);
        TextView note=label("Pobieraj podpisane paczki z katalogu Polish Fighters na GitHubie.",12,MUTED,false);
        note.setLineSpacing(dp(2),1f);side.addView(note,wrap());
        LinearLayout statusCard=new LinearLayout(this);statusCard.setOrientation(LinearLayout.VERTICAL);statusCard.setBackgroundResource(R.drawable.pf_loading_surface);statusCard.setPadding(dp(12),dp(9),dp(12),dp(9));
        status=label("Wybierz źródło albo zaimportuj paczkę LF2.",12,TEXT,false);status.setContentDescription("Status importu");status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        statusCard.addView(status,wrap());
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setIndeterminate(true);progress.setVisibility(View.GONE);
        LinearLayout.LayoutParams progressParams=new LinearLayout.LayoutParams(-1,dp(6));progressParams.topMargin=dp(6);statusCard.addView(progress,progressParams);
        LinearLayout.LayoutParams statusParams=wrap();statusParams.topMargin=dp(12);side.addView(statusCard,statusParams);
        side.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
        ClassicButton install=action("IMPORTUJ PACZKĘ ZIP",this::pickPackage);side.addView(install,new LinearLayout.LayoutParams(-1,dp(46)));
        ClassicButton back=action("< WSTECZ",this::goBack);LinearLayout.LayoutParams backParams=new LinearLayout.LayoutParams(-1,dp(46));backParams.topMargin=dp(8);side.addView(back,backParams);

        LinearLayout list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);list.setBackgroundResource(R.drawable.pf_loading_surface);list.setPadding(dp(12),dp(10),dp(12),dp(6));
        LinearLayout.LayoutParams listParams=new LinearLayout.LayoutParams(0,-1,1.08f);listParams.leftMargin=dp(18);page.addView(list,listParams);
        TextView sources=label("KATALOG MODÓW",12,BLUE,true);sources.setPadding(dp(2),0,0,dp(8));list.addView(sources,wrap());
        // Rows scroll inside the card and fade at its edges instead of being cut off mid-line.
        scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.setVerticalFadingEdgeEnabled(true);scroll.setFadingEdgeLength(dp(18));scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);scroll.addView(rows);list.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        if (getIntent().getBooleanExtra(FIRST_SETUP,false)) showSetup();
        else showSources();
    }

    private LinearLayout.LayoutParams wrap() { return new LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT); }
    private TextView label(String value,int size,int color,boolean bold) {
        TextView view=new TextView(this);view.setText(value);view.setTextColor(color);view.setTextSize(size);
        view.setTypeface(Typeface.MONOSPACE,bold?Typeface.BOLD:Typeface.NORMAL);return view;
    }
    private ClassicButton action(String label,Runnable click) {
        // The pixel font has no dashes or ellipsis; they would be drawn as "?".
        ClassicButton button=new ClassicButton(this);button.setText(label.replace("—","-").replace("–","-").replace("…","..."));button.setContentDescription(label);button.setAllCaps(false);button.setMinHeight(dp(44));button.setPadding(dp(8),dp(5),dp(8),dp(5));button.setBackgroundResource(R.drawable.pf_button);button.setBackgroundTintList(null);button.setOnClickListener(v->click.run());return button;
    }
    private int dp(int value) { return Math.round(value*getResources().getDisplayMetrics().density); }

    private void showSources() {
        previousScreen = null;
        scroll.scrollTo(0,0);
        rows.removeAllViews();
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
        scroll.scrollTo(0,0);
        rows.addView(label("KONFIGURACJA GRY",18,TEXT,true),wrap());
        for (int index : baseChoices) {
            rows.addView(action((setupBase==index ? "[X] " : "[ ] ")+GamePackSettings.TITLES[index],()->{
                if (importing) return;
                int offset=scroll.getScrollY();
                setupBase=index;showSetup();restoreScroll(offset);
            }),wrap());
        }
        rows.addView(label("DODATKI DO WSPÓLNEJ PULI",14,TEXT,true),wrap());
        for (int i=3;i<setupSelection.length;i++) {
            final int index=i;
            rows.addView(action((setupSelection[index] ? "[X] " : "[ ] ")+GamePackSettings.TITLES[index],()->{
                if (importing) return;
                int offset=scroll.getScrollY();
                setupSelection[index]=!setupSelection[index];showSetup();restoreScroll(offset);
            }),wrap());
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
        if(importing)return;setBusy(true,"Pobieram podpisany katalog: "+AndroidModSources.GITHUB_NAME);
        worker.submit(()->{
            try {
                List<AndroidModSources.Package> found=AndroidModSources.fetchGitHubCatalogue(trustedKey());
                runOnUiThread(()->showPackages(found,scroll.getScrollY()));
            }
            catch(Exception error) { runOnUiThread(()->setBusy(false,"Nie udało się pobrać katalogu. "+safe(error.getMessage()))); }
        });
    }
    private void showPackages(List<AndroidModSources.Package> found,int sourceOffset) {
        previousScreen = () -> { showSources(); restoreScroll(sourceOffset); };
        scroll.scrollTo(0,0);
        rows.removeAllViews();
        for(AndroidModSources.Package item:found) {
            String state = packageState(item);
            ClassicButton button=action(item.name+" "+item.version+" - "+item.sizeLabel(),
                    ()->showPackage(item,found,sourceOffset,scroll.getScrollY()));
            button.setContentDescription(item.name+", "+item.version+", "+item.sizeLabel()+", "+state);
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(button,params);
            rows.addView(label(state,12,MUTED,false),wrap());
        }
        ClassicButton back=action("WRÓĆ DO MODÓW",this::goBack);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(back,params);
        setBusy(false,"Podpis katalogu poprawny. Mody: "+found.size()+". Wybierz, aby pobrać i zainstalować.");
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
    private String packageState(AndroidModSources.Package item) {
        String receipt = installedReceipt(item);
        if (receipt == null) return "Do pobrania";
        if (receipt.equals(item.receipt())) return "Zainstalowano "+item.version;
        return receipt.isEmpty() ? "Zainstalowano — wersja nieznana" : "Dostępna aktualizacja";
    }
    private void showPackage(AndroidModSources.Package item,List<AndroidModSources.Package> catalogue,
            int sourceOffset,int catalogueOffset) {
        previousScreen = () -> { showPackages(catalogue,sourceOffset); restoreScroll(catalogueOffset); };
        scroll.scrollTo(0,0);
        rows.removeAllViews();
        rows.addView(label(item.name+" "+item.version,18,TEXT,true),wrap());
        rows.addView(label(item.description,14,TEXT,false),wrap());
        rows.addView(label("Pobieranie: "+item.sizeLabel()+" · "+packageState(item),12,MUTED,false),wrap());
        String receipt = installedReceipt(item);
        if (!item.receipt().equals(receipt)) {
            rows.addView(action(receipt == null ? "POBIERZ" : "POBIERZ WERSJĘ Z KATALOGU",
                    ()->install(item,catalogue,sourceOffset,catalogueOffset)),wrap());
        }
        rows.addView(action("WRÓĆ DO KATALOGU",this::goBack),wrap());
    }
    private void install(AndroidModSources.Package item,List<AndroidModSources.Package> catalogue,
            int sourceOffset,int catalogueOffset) {
        if(importing)return;
        if(item.receipt().equals(installedReceipt(item)))return;
        setBusy(true,"Przygotowuję pobieranie…");
        worker.submit(()->{
            try {
                transferAndInstall(item);
                String message="Zainstalowano "+item.name+" "+item.version+".";
                try {
                    GamePackSettings settings=new GamePackSettings(getFilesDir());
                    if(!item.profile.isEmpty()){settings.save(item.profile,settings.selection(),settings.hideDuplicates());message+=selectionMessage();}
                } catch(Exception saveError) { message+=" Wybierz go w menu Moduły."; }
                final String done=message;
                runOnUiThread(()->{setBusy(false,done);showPackage(item,catalogue,sourceOffset,catalogueOffset);});
            } catch(Exception error) {
                android.util.Log.w("OpenLF2","GitHub mod install failed",error);
                runOnUiThread(()->setBusy(false,"Instalacja przerwana: "+safe(error.getMessage())));
            }
        });
    }
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
                return !worker.isShutdown();
            });
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
                try { GamePackSettings settings=new GamePackSettings(getFilesDir());settings.save(id,settings.selection(),settings.hideDuplicates());runOnUiThread(()->setBusy(false,"Zaimportowano "+id+"."+selectionMessage()+" Zgodność gry nie jest potwierdzona.")); }
                catch(Exception saveError) { runOnUiThread(()->setBusy(false,"Paczka "+id+" jest zainstalowana, ale nie zapisano jej wyboru: "+safe(saveError.getMessage()))); }
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Import przerwany: "+safe(error.getMessage()))); }
        });
    }
    private String selectionMessage() {
        return getIntent().getBooleanExtra(FROM_RUNNING_GAME, false)
            ? " Wybór zapisany na następne uruchomienie gry."
            : " Moduł wybrany do gry.";
    }
    private void leave() { finish(); }
    private void restoreScroll(int offset) { scroll.post(() -> scroll.scrollTo(0,offset)); }
    private void goBack() {
        if (importing) return;
        if (previousScreen == null) leave();
        else previousScreen.run();
    }
    @Override public void onBackPressed() { goBack(); }
    private void setBusy(boolean busy,String message) { importing=busy;status.setText(message);if(!busy)progress.setIndeterminate(true);progress.setVisibility(busy?View.VISIBLE:View.GONE); }
    private static String safe(String value) { if(value==null)return "nieznany błąd";String text=value.replaceAll("[\\r\\n\\p{Cntrl}]"," ");return text.substring(0,Math.min(text.length(),240)); }
    @Override protected void onDestroy() { worker.shutdownNow();super.onDestroy(); }
}
