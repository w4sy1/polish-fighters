package io.github.openlf2.openlf2;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import android.widget.LinearLayout;

/** Keeps the classic centred column narrow on desktop-sized screens and inside small phones. */
public final class ClassicColumn extends LinearLayout {
    public ClassicColumn(Context context,AttributeSet attrs) {super(context,attrs);}
    @Override protected void onMeasure(int widthSpec,int heightSpec) {
        int limit=Math.round(340*getResources().getDisplayMetrics().density);
        int available=View.MeasureSpec.getSize(widthSpec);
        super.onMeasure(View.MeasureSpec.makeMeasureSpec(Math.min(limit,available),View.MeasureSpec.EXACTLY),heightSpec);
    }
}
