package io.github.openlf2.openlf2;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** LF2-styled source browser and file-picker importer for converted packages. */
public final class AndroidModsActivity extends Activity {
    private static final int PICK_PACKAGE=7301;
    private static final int NAVY=0xff040a41, PANEL=0xff102164, BLUE=0xff4f9bff, TEXT=0xfff4f5ff, MUTED=0xffb6c5d9;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout rows;
    private TextView status;
    private ProgressBar progress;
    private boolean importing;

    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(18),dp(12),dp(18),dp(10));page.setBackgroundColor(NAVY);
        TextView title=new TextView(this);title.setText("MODS / MODUŁY");title.setTextColor(TEXT);title.setTextSize(20);title.setTypeface(Typeface.MONOSPACE,Typeface.BOLD);title.setGravity(android.view.Gravity.CENTER);page.addView(title,new LinearLayout.LayoutParams(-1,dp(34)));
        View rule=new View(this);rule.setBackgroundColor(BLUE);page.addView(rule,new LinearLayout.LayoutParams(-1,dp(2)));
        TextView note=body("Katalog otwiera strony projektów. ZIP pobierasz ze strony i wskazujesz tutaj.");
        note.setPadding(dp(10),dp(7),dp(10),dp(7));note.setBackground(panel());
        LinearLayout.LayoutParams noteParams=new LinearLayout.LayoutParams(-1,dp(48));noteParams.topMargin=dp(9);page.addView(note,noteParams);
        status=body("Wybierz źródło albo zaimportuj paczkę LF2.");status.setContentDescription("Status importu");status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        status.setPadding(dp(8),dp(5),dp(8),dp(5));page.addView(status,new LinearLayout.LayoutParams(-1,dp(38)));
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setIndeterminate(true);progress.setVisibility(View.GONE);page.addView(progress,new LinearLayout.LayoutParams(-1,dp(4)));
        ClassicButton install=action("IMPORTUJ PACZKĘ ZIP",this::pickPackage);LinearLayout.LayoutParams installParams=new LinearLayout.LayoutParams(-1,dp(48));installParams.topMargin=dp(4);page.addView(install,installParams);
        TextView sources=body("ŹRÓDŁA MODÓW");sources.setTextColor(BLUE);sources.setTypeface(Typeface.MONOSPACE,Typeface.BOLD);sources.setPadding(dp(4),dp(5),0,0);page.addView(sources,new LinearLayout.LayoutParams(-1,dp(28)));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);scroll.addView(rows);page.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        ClassicButton back=action("POWRÓT",this::finish);LinearLayout.LayoutParams backParams=new LinearLayout.LayoutParams(-1,dp(44));backParams.topMargin=dp(5);page.addView(back,backParams);
        setContentView(page);
        for(AndroidModSources.Source source:AndroidModSources.SOURCES) addSource(source);
    }

    private TextView body(String value) {
        TextView view=new TextView(this);view.setText(value);view.setTextColor(MUTED);view.setTextSize(12);view.setTypeface(Typeface.MONOSPACE);view.setGravity(android.view.Gravity.CENTER_VERTICAL);return view;
    }
    private GradientDrawable panel() {
        GradientDrawable drawable=new GradientDrawable();drawable.setColor(PANEL);drawable.setCornerRadius(dp(3));drawable.setStroke(dp(1),BLUE);return drawable;
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
        rows.removeAllViews();for(AndroidModSources.Source source:AndroidModSources.SOURCES)addSource(source);
        status.setText("Wybierz źródło. ZIP pobierz ze strony, a potem zaimportuj.");
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
                String id=AndroidModPackageImporter.importPackage(getContentResolver(),selected,getFilesDir(),entries->runOnUiThread(()->status.setText("Sprawdzono plików: "+entries)));
                try { GamePackSettings settings=new GamePackSettings(getFilesDir());settings.save(id,settings.selection(),settings.hideDuplicates());runOnUiThread(()->setBusy(false,"Zaimportowano "+id+". Moduł został wybrany; zgodność gry nie jest potwierdzona.")); }
                catch(Exception saveError) { runOnUiThread(()->setBusy(false,"Paczka "+id+" jest zainstalowana, ale nie zapisano jej wyboru: "+safe(saveError.getMessage()))); }
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Import przerwany: "+safe(error.getMessage()))); }
        });
    }
    private void setBusy(boolean busy,String message) { importing=busy;status.setText(message);progress.setVisibility(busy?View.VISIBLE:View.GONE); }
    private static String safe(String value) { if(value==null)return "nieznany błąd";String text=value.replaceAll("[\\r\\n\\p{Cntrl}]"," ");return text.substring(0,Math.min(text.length(),240)); }
    @Override protected void onDestroy() { worker.shutdownNow();super.onDestroy(); }
}
