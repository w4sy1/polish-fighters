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
    static final String RETURN_TO_GAME="return_to_game";
    private static final int PICK_PACKAGE=7301;
    private static final int NAVY=0xff040a41, BLUE=0xff7a9dff, RED=0xffff5262, TEXT=0xfff4f5ff, MUTED=0xffb6c5d9;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout rows;
    private TextView status;
    private ProgressBar progress;
    private boolean importing;

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
        TextView note=label("Mody z GitHuba gra pobiera i instaluje sama, po sprawdzeniu podpisu. Inne źródła otwierają się w przeglądarce.",12,MUTED,false);
        note.setLineSpacing(dp(2),1f);side.addView(note,wrap());
        LinearLayout statusCard=new LinearLayout(this);statusCard.setOrientation(LinearLayout.VERTICAL);statusCard.setBackgroundResource(R.drawable.pf_loading_surface);statusCard.setPadding(dp(12),dp(9),dp(12),dp(9));
        status=label("Wybierz źródło albo zaimportuj paczkę LF2.",12,TEXT,false);status.setContentDescription("Status importu");status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        statusCard.addView(status,wrap());
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setIndeterminate(true);progress.setVisibility(View.GONE);
        LinearLayout.LayoutParams progressParams=new LinearLayout.LayoutParams(-1,dp(6));progressParams.topMargin=dp(6);statusCard.addView(progress,progressParams);
        LinearLayout.LayoutParams statusParams=wrap();statusParams.topMargin=dp(12);side.addView(statusCard,statusParams);
        side.addView(new View(this),new LinearLayout.LayoutParams(1,0,1));
        ClassicButton install=action("IMPORTUJ PACZKĘ ZIP",this::pickPackage);side.addView(install,new LinearLayout.LayoutParams(-1,dp(46)));
        ClassicButton back=action("POWRÓT",this::leave);LinearLayout.LayoutParams backParams=new LinearLayout.LayoutParams(-1,dp(46));backParams.topMargin=dp(8);side.addView(back,backParams);

        LinearLayout list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);list.setBackgroundResource(R.drawable.pf_loading_surface);list.setPadding(dp(12),dp(10),dp(12),dp(6));
        LinearLayout.LayoutParams listParams=new LinearLayout.LayoutParams(0,-1,1.08f);listParams.leftMargin=dp(18);page.addView(list,listParams);
        TextView sources=label("ŹRÓDŁA MODÓW",12,BLUE,true);sources.setPadding(dp(2),0,0,dp(8));list.addView(sources,wrap());
        // Rows scroll inside the card and fade at its edges instead of being cut off mid-line.
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.setVerticalFadingEdgeEnabled(true);scroll.setFadingEdgeLength(dp(18));scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);scroll.addView(rows);list.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        showSources();
    }

    private LinearLayout.LayoutParams wrap() { return new LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT); }
    private TextView label(String value,int size,int color,boolean bold) {
        TextView view=new TextView(this);view.setText(value);view.setTextColor(color);view.setTextSize(size);
        view.setTypeface(Typeface.MONOSPACE,bold?Typeface.BOLD:Typeface.NORMAL);return view;
    }
    private ClassicButton action(String label,Runnable click) {
        ClassicButton button=new ClassicButton(this);button.setText(label);button.setAllCaps(false);button.setMinHeight(dp(44));button.setPadding(dp(8),dp(5),dp(8),dp(5));button.setBackgroundResource(R.drawable.pf_button);button.setBackgroundTintList(null);button.setOnClickListener(v->click.run());return button;
    }
    private int dp(int value) { return Math.round(value*getResources().getDisplayMetrics().density); }

    private void addSource(AndroidModSources.Source source) {
        ClassicButton button=action("PRZEGLĄDAJ: "+source.name,()->discover(source));
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,dp(44));params.bottomMargin=dp(4);rows.addView(button,params);
    }
    private void discover(AndroidModSources.Source source) {
        if(importing)return;setBusy(true,"Sprawdzam źródło: "+source.name);
        worker.submit(()->{
            try { List<AndroidModSources.Candidate> found=AndroidModSources.discover(source);runOnUiThread(()->showCandidates(source,found)); }
            catch(Exception error) { runOnUiThread(()->setBusy(false,"Nie udało się pobrać listy. "+safe(error.getMessage()))); }
        });
    }
    private void showCandidates(AndroidModSources.Source source,List<AndroidModSources.Candidate> found) {
        rows.removeAllViews();
        status.setText(found.isEmpty()?"Brak rozpoznanych wpisów. Możesz otworzyć stronę źródła.":"Znaleziono "+found.size()+" wpisów. Otwierane są strony projektów.");
        for(AndroidModSources.Candidate candidate:found) {
            ClassicButton button=action(candidate.label,()->openPage(candidate.url,source.host));
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(button,params);
        }
        ClassicButton open=action("OTWÓRZ STRONĘ ŹRÓDŁA",()->openPage(source.page,source.host));
        ClassicButton back=action("WRÓĆ DO ŹRÓDEŁ",()->showSources());
        for(ClassicButton button:new ClassicButton[]{open,back}) {LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(button,params);}
        setBusy(false,status.getText().toString());
    }
    private void showSources() {
        rows.removeAllViews();
        ClassicButton github=action("POBIERZ: "+AndroidModSources.GITHUB_NAME.replace("—","-"),this::showGitHub);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(github,params);
        for(AndroidModSources.Source source:AndroidModSources.SOURCES)addSource(source);
        status.setText("Wybierz źródło albo zaimportuj paczkę LF2.");
    }
    private byte[] trustedKey() throws java.io.IOException {
        try(java.io.InputStream key=getAssets().open(SignedModPackage.KEY_ASSET)){return SignedModPackage.read(key,32);}
    }
    private void showGitHub() {
        if(importing)return;setBusy(true,"Pobieram podpisany katalog: "+AndroidModSources.GITHUB_NAME);
        worker.submit(()->{
            try { List<AndroidModSources.Package> found=AndroidModSources.fetchGitHubCatalogue(trustedKey());runOnUiThread(()->showPackages(found)); }
            catch(Exception error) { runOnUiThread(()->setBusy(false,"Nie udało się pobrać katalogu. "+safe(error.getMessage()))); }
        });
    }
    private void showPackages(List<AndroidModSources.Package> found) {
        rows.removeAllViews();
        for(AndroidModSources.Package item:found) {
            boolean installed=new java.io.File(getFilesDir(),"game/content-packs/"+item.id+"/package.manifest").isFile();
            ClassicButton button=action((installed?"OK: ":"")+item.name+" - "+item.sizeLabel(),()->install(item));
            button.setContentDescription("Pobierz i zainstaluj "+item.name);
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(button,params);
        }
        ClassicButton back=action("WRÓĆ DO ŹRÓDEŁ",this::showSources);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(44));params.bottomMargin=dp(4);rows.addView(back,params);
        setBusy(false,"Podpis katalogu poprawny. Mody: "+found.size()+". Wybierz, aby pobrać i zainstalować.");
    }
    private void install(AndroidModSources.Package item) {
        if(importing)return;
        java.io.File folder=new java.io.File(getCacheDir(),"mods");
        if(!folder.isDirectory()&&!folder.mkdirs()){setBusy(false,"Nie można przygotować katalogu pobierania.");return;}
        long needed=2*item.size+item.unpacked+64L*1024*1024;
        if(getFilesDir().getFreeSpace()<needed){setBusy(false,"Za mało miejsca: potrzeba około "+(needed>>20)+" MB.");return;}
        setBusy(true,"Pobieram "+item.name+"…");progress.setIndeterminate(false);progress.setMax(1000);progress.setProgress(0);
        worker.submit(()->{
            java.io.File envelope=new java.io.File(folder,item.id+"-"+item.version+".zip");
            try {
                final long[] shown={-1};
                AndroidModSources.download(item,envelope,(received,total)->{
                    long permille=total>0?received*1000/total:0;
                    if(permille!=shown[0]){shown[0]=permille;runOnUiThread(()->{progress.setProgress((int)permille);
                        status.setText("Pobieram "+item.name+": "+(received>>20)+" / "+(total>>20)+" MB ("+permille/10+"%)");});}
                    return !worker.isShutdown();
                });
                runOnUiThread(()->{progress.setIndeterminate(true);status.setText("Sprawdzam podpis i instaluję "+item.name+"…");});
                String id=AndroidModPackageImporter.importDownloaded(envelope,getFilesDir(),getAssets(),item.id,
                    files->runOnUiThread(()->status.setText("Instaluję "+item.name+": plików "+files)));
                String message="Zainstalowano "+item.name+" "+item.version+".";
                try {
                    GamePackSettings settings=new GamePackSettings(getFilesDir());
                    if(!item.profile.isEmpty()){settings.save(item.profile,settings.selection(),settings.hideDuplicates());message+=" Moduł wybrany do gry.";}
                } catch(Exception saveError) { message+=" Wybierz go w menu Moduły."; }
                final String done=message;
                runOnUiThread(()->{setBusy(false,done);showPackagesAgain();});
                android.util.Log.i("OpenLF2","GitHub mod installed: "+id);
            } catch(Exception error) {
                android.util.Log.w("OpenLF2","GitHub mod install failed",error);
                runOnUiThread(()->setBusy(false,"Instalacja przerwana: "+safe(error.getMessage())));
            } finally { envelope.delete(); }
        });
    }
    private void showPackagesAgain() {
        worker.submit(()->{
            try { List<AndroidModSources.Package> found=AndroidModSources.fetchGitHubCatalogue(trustedKey());
                runOnUiThread(()->{String keep=status.getText().toString();showPackages(found);status.setText(keep);}); }
            catch(Exception ignored) {}
        });
    }
    private void openPage(String address,String host) {
        try { Uri uri=Uri.parse(address);if(!"https".equals(uri.getScheme())||!host.equalsIgnoreCase(uri.getHost()))throw new IllegalArgumentException();startActivity(new Intent(Intent.ACTION_VIEW,uri)); }
        catch(Exception error) { setBusy(false,"Nie można otworzyć strony w zaufanej domenie."); }
    }
    private void pickPackage() {
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
                try { GamePackSettings settings=new GamePackSettings(getFilesDir());settings.save(id,settings.selection(),settings.hideDuplicates());runOnUiThread(()->setBusy(false,"Zaimportowano "+id+". Moduł został wybrany; zgodność gry nie jest potwierdzona.")); }
                catch(Exception saveError) { runOnUiThread(()->setBusy(false,"Paczka "+id+" jest zainstalowana, ale nie zapisano jej wyboru: "+safe(saveError.getMessage()))); }
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Import przerwany: "+safe(error.getMessage()))); }
        });
    }
    private void leave() {
        if(getIntent().getBooleanExtra(RETURN_TO_GAME,false)) startActivity(new Intent(this,OpenLF2Activity.class));
        finish();
    }
    @Override public void onBackPressed() { leave(); }
    private void setBusy(boolean busy,String message) { importing=busy;status.setText(message);if(!busy)progress.setIndeterminate(true);progress.setVisibility(busy?View.VISIBLE:View.GONE); }
    private static String safe(String value) { if(value==null)return "nieznany błąd";String text=value.replaceAll("[\\r\\n\\p{Cntrl}]"," ");return text.substring(0,Math.min(text.length(),240)); }
    @Override protected void onDestroy() { worker.shutdownNow();super.onDestroy(); }
}
