package io.github.openlf2.openlf2;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import java.lang.ref.WeakReference;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;

/** A bounded, anonymous check; installation always remains the player's choice. */
final class GitHubUpdates {
    interface Source { String fetch() throws Exception; }
    static Source source = GitHubUpdates::fetch;
    private static boolean started, delivered;
    private static String available;
    private static WeakReference<Activity> current = new WeakReference<>(null);
    private static final String RELEASES = "https://github.com/w4sy1/polish-fighters/releases/";

    static long version(String text) {
        Matcher m = Pattern.compile("(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})").matcher(text);
        return m.find() ? Long.parseLong(m.group(1))*1000000L + Long.parseLong(m.group(2))*1000L + Long.parseLong(m.group(3)) : 0;
    }

    static String select(String json, String installed) throws Exception {
        JSONArray releases = new JSONArray(json);
        long best = version(installed);
        String result = null;
        for (int i=0; i<releases.length(); i++) {
            JSONObject r = releases.optJSONObject(i);
            if (r==null || r.optBoolean("draft") || !r.optString("html_url").startsWith(RELEASES+"tag/")) continue;
            boolean apk = false;
            JSONArray assets = r.optJSONArray("assets");
            if (assets != null) for (int a=0; a<assets.length(); a++) {
                JSONObject asset = assets.optJSONObject(a);
                if (asset!=null && asset.optString("name").toLowerCase(java.util.Locale.ROOT).endsWith(".apk") &&
                    "uploaded".equals(asset.optString("state"))) apk=true;
            }
            long candidate = version(r.optString("name"));
            if (candidate==0) candidate=version(r.optString("tag_name"));
            if (apk && candidate>best) { best=candidate; result=r.optString("html_url"); }
        }
        return result;
    }

    static void attach(Activity activity) {
        current = new WeakReference<>(activity);
        if (!started) {
            started=true;
            final Source fetcher=source;
            final String installed;
            try { installed=activity.getPackageManager().getPackageInfo(activity.getPackageName(),0).versionName; }
            catch (Exception ignored) { return; }
            Thread worker=new Thread(() -> {
                String found=null;
                try { String json=fetcher.fetch(); if (json!=null) found=select(json,installed); }
                catch (Exception ignored) { /* Offline/rate limits must not interrupt play. */ }
                final String selected=found;
                new Handler(Looper.getMainLooper()).post(() -> { available=selected; show(); });
            },"PolishFighters-updates");
            worker.setDaemon(true);
            worker.start();
        }
        show();
    }

    private static void show() {
        Activity activity=current.get();
        if (available==null || delivered || activity==null || activity.isFinishing() || activity.isDestroyed()) return;
        delivered=true;
        final String link=available;
        new AlertDialog.Builder(activity).setTitle("Dostępna aktualizacja Polish Fighters")
            .setMessage("Na GitHubie jest nowsza wersja gry. Otworzyć stronę pobierania?")
            .setPositiveButton("Pobierz",(d,w) -> {
                try { activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(link))); }
                catch (android.content.ActivityNotFoundException ignored) {
                    android.widget.Toast.makeText(activity,"Nie znaleziono przeglądarki",android.widget.Toast.LENGTH_LONG).show();
                }
            }).setNegativeButton("Później",null).show();
    }

    private static String fetch() throws Exception {
        HttpURLConnection connection=(HttpURLConnection)new URL("https://api.github.com/repos/w4sy1/polish-fighters/releases?per_page=5").openConnection();
        connection.setConnectTimeout(3000); connection.setReadTimeout(5000);
        connection.setInstanceFollowRedirects(false);
        connection.setRequestProperty("User-Agent","PolishFighters-UpdateCheck/1");
        connection.setRequestProperty("Accept","application/vnd.github+json");
        try {
            if (connection.getResponseCode()!=200) return null;
            try (InputStream stream=connection.getInputStream(); ByteArrayOutputStream bytes=new ByteArrayOutputStream()) {
                byte[] buffer=new byte[8192]; int n;
                while ((n=stream.read(buffer))!=-1) {
                    if (bytes.size()+n>524288) return null;
                    bytes.write(buffer,0,n);
                }
                return bytes.toString("UTF-8");
            }
        } finally { connection.disconnect(); }
    }

    static void resetForTest() {
        started=false; delivered=false; available=null; current.clear(); source=()->null;
    }
}
