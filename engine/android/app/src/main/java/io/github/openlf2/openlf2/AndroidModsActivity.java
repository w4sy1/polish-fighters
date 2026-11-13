package io.github.openlf2.openlf2;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Android source browser and system-file-picker importer for converted LF2 data packages. */
public final class AndroidModsActivity extends Activity {
    private static final int PICK_PACKAGE=7301;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout rows;
    private TextView status;
    private ProgressBar progress;
    private boolean importing;

    @Override protected void attachBaseContext(android.content.Context base) { super.attachBaseContext(ClassicMenuData.localized(base)); }
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(20,18,20,12);
        page.setBackgroundColor(0xff101a2b);
        TextView title=new TextView(this);title.setText("MOD BROWSER / IMPORTER");title.setTextColor(0xfff4f5ff);title.setTextSize(21);page.addView(title);
        TextView note=new TextView(this);note.setText("Źródła pokazują publiczne strony projektów. Zgodność i bezpośrednie pliki nie są potwierdzone. Import obsługuje ZIP z konwertera LF2.");note.setTextColor(0xffc0d0ef);note.setPadding(0,8,0,10);page.addView(note);
        status=new TextView(this);status.setText("Wybierz źródło albo zaimportuj obsługiwaną paczkę ZIP.");status.setTextColor(0xffd9e4ff);page.addView(status);
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setIndeterminate(true);progress.setVisibility(android.view.View.GONE);page.addView(progress);
        Button install=new Button(this);install.setText("IMPORTUJ PACZKĘ ZIP");install.setOnClickListener(v->pickPackage());page.addView(install);
        ScrollView scroll=new ScrollView(this);rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);scroll.addView(rows);page.addView(scroll,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1));
        Button back=new Button(this);back.setText("POWRÓT");back.setOnClickListener(v->finish());page.addView(back);
        setContentView(page);
        for(AndroidModSources.Source source:AndroidModSources.SOURCES) addSource(source);
    }

    private void addSource(AndroidModSources.Source source) {
        Button button=new Button(this);button.setText("PRZEGLĄDAJ: "+source.name);rows.addView(button);
        button.setOnClickListener(v->discover(source));
    }
    private void discover(AndroidModSources.Source source) {
        if(importing)return; setBusy(true,"Sprawdzam źródło: "+source.name);
        worker.submit(()->{
            try {
                List<AndroidModSources.Candidate> found=AndroidModSources.discover(source);
                runOnUiThread(()->showCandidates(source,found));
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Nie udało się pobrać listy. "+safe(error.getMessage()))); }
        });
    }
    private void showCandidates(AndroidModSources.Source source,List<AndroidModSources.Candidate> found) {
        setBusy(false,found.isEmpty()?"Źródło nie udostępniło rozpoznanych wpisów; otwórz stronę ręcznie.":"Znaleziono "+found.size()+" wpisów. Otwierają wyłącznie strony projektów.");
        for(AndroidModSources.Candidate candidate:found) {
            Button button=new Button(this);button.setText(candidate.label);rows.addView(button);
            button.setOnClickListener(v->openPage(candidate.url,source.host));
        }
        Button open=new Button(this);open.setText("OTWÓRZ STRONĘ ŹRÓDŁA");rows.addView(open);open.setOnClickListener(v->openPage(source.page,source.host));
    }
    private void openPage(String address,String host) {
        try {
            Uri uri=Uri.parse(address);
            if(!"https".equals(uri.getScheme())||!host.equalsIgnoreCase(uri.getHost()))throw new IllegalArgumentException();
            startActivity(new Intent(Intent.ACTION_VIEW,uri));
        } catch(Exception error) { setBusy(false,"Nie można otworzyć zweryfikowanej domeny źródła."); }
    }
    private void pickPackage() {
        Intent request=new Intent(Intent.ACTION_OPEN_DOCUMENT);request.setType("application/zip");request.addCategory(Intent.CATEGORY_OPENABLE);
        request.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try { startActivityForResult(request,PICK_PACKAGE); }
        catch(Exception error) { setBusy(false,"Systemowy selektor plików jest niedostępny."); }
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=PICK_PACKAGE||resultCode!=RESULT_OK||data==null||data.getData()==null)return;
        Uri selected=data.getData();setBusy(true,"Sprawdzam i importuję paczkę…");
        worker.submit(()->{
            try {
                String id=AndroidModPackageImporter.importPackage(getContentResolver(),selected,getFilesDir(),entries->runOnUiThread(()->status.setText("Sprawdzono wpisów: "+entries)));
                try {
                    GamePackSettings settings=new GamePackSettings(getFilesDir());settings.save(id,settings.selection(),settings.hideDuplicates());
                    runOnUiThread(()->setBusy(false,"Zaimportowano "+id+". Moduł wybrano w MODUŁY; zgodność gry nie jest potwierdzona."));
                } catch(Exception saveError) {
                    runOnUiThread(()->setBusy(false,"Paczka "+id+" jest zainstalowana, ale nie zapisano jej wyboru: "+safe(saveError.getMessage())));
                }
            } catch(Exception error) { runOnUiThread(()->setBusy(false,"Import przerwany: "+safe(error.getMessage()))); }
        });
    }
    private void setBusy(boolean busy,String message) {
        importing=busy;status.setText(message);progress.setVisibility(busy?android.view.View.VISIBLE:android.view.View.GONE);
    }
    private static String safe(String value) { if(value==null)return "nieznany błąd";String text=value.replaceAll("[\\r\\n\\p{Cntrl}]"," ");return text.substring(0,Math.min(text.length(),240)); }
    @Override protected void onDestroy() { worker.shutdownNow();super.onDestroy(); }
}
