package io.github.openlf2.openlf2;

import android.content.Context;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

final class ClassicMenuData {
    private static JSONObject data;
    static synchronized JSONObject read(Context context) {
        if (data != null) return data;
        try (InputStream input=context.getAssets().open("classic-menu.json")) {
            ByteArrayOutputStream output=new ByteArrayOutputStream();byte[] block=new byte[4096];int n;
            while((n=input.read(block))!=-1) output.write(block,0,n);
            data=new JSONObject(new String(output.toByteArray(),StandardCharsets.UTF_8));
            return data;
        } catch (java.io.IOException | org.json.JSONException error) {
            throw new IllegalStateException("Missing generated classic menu data",error);
        }
    }
    static String text(Context context,String language,String key) {
        return read(context).optJSONObject(language).optString(key,key);
    }
    static Context localized(Context context) {
        String language="pl";
        try {
            JSONObject options=new MobileCodeSettings(context.getFilesDir()).read().optJSONObject("options");
            if(options!=null && "english".equals(options.optString("language")))language="en";
        } catch(java.io.IOException | org.json.JSONException ignored) {
            // The activity's normal settings reader reports malformed user data.
        }
        android.content.res.Configuration config=new android.content.res.Configuration(context.getResources().getConfiguration());
        config.setLocale(java.util.Locale.forLanguageTag(language));
        return context.createConfigurationContext(config);
    }
    private ClassicMenuData() {}
}
