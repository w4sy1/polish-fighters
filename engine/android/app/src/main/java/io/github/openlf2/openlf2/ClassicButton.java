package io.github.openlf2.openlf2;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.widget.Button;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/** Native clickable/focusable button, painted with the same project-owned glyphs as Lua. */
public final class ClassicButton extends Button {
    private static final JSONArray MIDDLE_DOT = new JSONArray().put(0).put(0).put(0).put(4);
    private static final JSONArray LEFT_CHEVRON = new JSONArray().put(0).put(2).put(4).put(8).put(4).put(2);
    private final Paint paint = new Paint();
    private boolean menuRow;
    public ClassicButton(Context context) { this(context,null); }
    public ClassicButton(Context context, AttributeSet attrs) { super(context, attrs); }
    void setMenuRowStyle() {
        menuRow = true;
        setBackgroundTintList(null);
        android.graphics.drawable.StateListDrawable background = new android.graphics.drawable.StateListDrawable();
        background.addState(new int[]{android.R.attr.state_pressed}, new android.graphics.drawable.ColorDrawable(0xff2a4786));
        background.addState(new int[]{android.R.attr.state_focused}, new android.graphics.drawable.ColorDrawable(0xff20396e));
        background.addState(new int[]{}, new android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT));
        setBackground(background);
    }
    @Override public boolean onKeyDown(int keyCode,android.view.KeyEvent event) {
        if(keyCode==android.view.KeyEvent.KEYCODE_BUTTON_A && isEnabled()) {setPressed(true);return true;}
        return super.onKeyDown(keyCode,event);
    }
    @Override public boolean onKeyUp(int keyCode,android.view.KeyEvent event) {
        if(keyCode==android.view.KeyEvent.KEYCODE_BUTTON_A && isEnabled()) {setPressed(false);performClick();return true;}
        return super.onKeyUp(keyCode,event);
    }
    @Override protected void onDraw(Canvas canvas) {
        String value = getText().toString().toUpperCase(Locale.ROOT);
        JSONObject data = ClassicMenuData.read(getContext());
        JSONObject glyphs = data.optJSONObject("glyphs"), accents = data.optJSONObject("accents");
        if (glyphs == null || accents == null) { super.onDraw(canvas); return; }
        float density = getResources().getDisplayMetrics().density;
        float scale = Math.min((menuRow ? 1.35f : 2f) * density,
            Math.min((getWidth() - 24 * density) / Math.max(1, value.length() * 6 - 1), (getHeight() - 12f) / 11f));
        float x = (getWidth() - (value.length() * 6 - 1) * scale) / 2;
        float y = (getHeight() - 7 * scale) / 2;
        int color = 0xfff4f5ff;
        if (!isEnabled()) color = 0xff7b8cbd;
        else if (menuRow && isActivated()) color = 0xffffdc82;
        else if (menuRow && !isPressed() && !isFocused()) color = 0xff81baf0;
        paint.setAntiAlias(false);
        paint.setColor(color);
        for (int i = 0; i < value.length(); i++) {
            String key = value.substring(i, i + 1);
            JSONArray rows = glyphs.optJSONArray(accents.optString(key, key));
            if ("·".equals(key)) rows = MIDDLE_DOT;
            else if ("<".equals(key)) rows = LEFT_CHEVRON;
            if (rows == null) rows = glyphs.optJSONArray("?");
            for (int row = 0; row < rows.length(); row++)
                for (int column = 0; column < 5; column++)
                    if ((rows.optInt(row) & (1 << (4 - column))) != 0) pixel(canvas, x, y, column, row, scale);
            if (key.equals("Ł")) { pixel(canvas,x,y,1,4,scale);pixel(canvas,x,y,3,2,scale); }
            else if (key.equals("Ą") || key.equals("Ę")) {pixel(canvas,x,y,3,7,scale);pixel(canvas,x,y,4,8,scale);}
            else if (key.equals("Ż")) pixel(canvas,x,y,2,-2,scale);
            else if (accents.has(key)) {pixel(canvas,x,y,2,-2,scale);pixel(canvas,x,y,3,-3,scale);}
            x += 6 * scale;
        }
    }
    private void pixel(Canvas canvas,float x,float y,int column,int row,float scale) {
        canvas.drawRect(x+column*scale,y+row*scale,x+(column+1)*scale,y+(row+1)*scale,paint);
    }
}
