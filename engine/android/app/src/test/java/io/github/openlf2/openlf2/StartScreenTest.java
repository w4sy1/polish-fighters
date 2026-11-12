package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.*;
import android.widget.*;
import java.io.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowAlertDialog;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,qualifiers="w800dp-h360dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class StartScreenTest {
 @Before public void offlineUpdates(){GitHubUpdates.resetForTest();}
 private void render(View view,String name) throws Exception {
  view.measure(View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY));
  view.layout(0,0,800,360);
  assertTrue(view.findViewById(R.id.pf_status).getWidth()>0);
  String directory=System.getenv("PF_SCREENSHOTS");
  if(directory!=null){File folder=new File(directory);assertTrue(folder.isDirectory()||folder.mkdirs());Bitmap bitmap=Bitmap.createBitmap(800,360,Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));try(FileOutputStream output=new FileOutputStream(new File(folder,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,output));}bitmap.recycle();}
 }
 @Test public void homeShowsSelectedGameAndStartsLocalPlay() throws Exception {
  try(ActivityController<BluetoothLobbyActivity> controller=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   BluetoothLobbyActivity activity=controller.get();View root=activity.findViewById(R.id.pf_screen);render(root,"home");
   Button play=activity.findViewById(R.id.pf_play);assertTrue(play.getWidth()>=200);assertTrue(play.getHeight()>=24);
   assertEquals(View.GONE,activity.findViewById(R.id.pf_cancel).getVisibility());
   assertEquals("MODUŁY",((Button)activity.findViewById(R.id.pf_module)).getText().toString());
   assertTrue(((TextView)activity.findViewById(R.id.pf_status)).getText().toString().startsWith("AKTYWNY MODUŁ:"));
   play.performClick();assertEquals("battle",new MobileCodeSettings(activity.getFilesDir()).read().getString("little_fighters_start_menu"));Intent next=Shadows.shadowOf(activity).getNextStartedActivity();assertTrue(next.getComponent().getClassName().endsWith("OpenLF2Activity"));
  }
 }
 @Test public void networkModesAreAvailableBehindOneHomeAction() throws Exception {
  try(ActivityController<BluetoothLobbyActivity> controller=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   BluetoothLobbyActivity activity=controller.get();activity.findViewById(R.id.pf_network).performClick();
   android.app.AlertDialog dialog=ShadowAlertDialog.getLatestAlertDialog();assertNotNull(dialog);assertEquals(6,dialog.getListView().getAdapter().getCount());
  }
 }
 @Test public void languageChangesImmediatelyAndPersistsAcrossActivities() throws Exception {
  try(ActivityController<BluetoothLobbyActivity> c=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   BluetoothLobbyActivity a=c.get();a.findViewById(R.id.pf_en).performClick();
   assertEquals("BATTLE",((Button)a.findViewById(R.id.pf_play)).getText().toString());
   assertEquals("english",new MobileCodeSettings(a.getFilesDir()).read().getJSONObject("options").getString("language"));
   assertEquals("Loading game data",ClassicMenuData.localized(a).getString(R.string.pf_loading_title));
   render(a.findViewById(R.id.pf_screen),"home-en");
  }
  try(ActivityController<BluetoothLobbyActivity> c=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   BluetoothLobbyActivity a=c.get();assertEquals("MODULES",((Button)a.findViewById(R.id.pf_module)).getText().toString());
   a.findViewById(R.id.pf_pl).performClick();assertEquals("BITWA",((Button)a.findViewById(R.id.pf_play)).getText().toString());
  }
 }
 @Test public void allSevenActionsFitSmallLandscapeAndPortrait() throws Exception {
  try(ActivityController<BluetoothLobbyActivity> c=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   View root=c.get().findViewById(R.id.pf_screen);
   for(int[] size:new int[][]{{640,360},{320,480},{360,640},{1280,720}}){
    root.measure(View.MeasureSpec.makeMeasureSpec(size[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(size[1],View.MeasureSpec.EXACTLY));root.layout(0,0,size[0],size[1]);
    for(int id:new int[]{R.id.pf_play,R.id.pf_module,R.id.pf_network,R.id.pf_settings,R.id.pf_language,R.id.pf_credits,R.id.pf_quit}){
     View b=root.findViewById(id);assertTrue(b.getHeight()>=24);assertTrue(b.getWidth()<=size[0]);assertTrue(b.getBottom()<=size[1]);
    }
   }
  }
 }
 @Test public void gamepadAActivatesFocusedBattleButton() throws Exception {
  try(ActivityController<BluetoothLobbyActivity> c=Robolectric.buildActivity(BluetoothLobbyActivity.class).setup()){
   BluetoothLobbyActivity a=c.get();View button=a.findViewById(R.id.pf_play);button.requestFocus();
   assertTrue(button.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_BUTTON_A)));
   assertTrue(button.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,KeyEvent.KEYCODE_BUTTON_A)));
   assertEquals("battle",new MobileCodeSettings(a.getFilesDir()).read().getString("little_fighters_start_menu"));
   assertNotNull(Shadows.shadowOf(a).getNextStartedActivity());
  }
 }
 @Test public void loadingAndErrorUseNewLayout() throws Exception {
  android.content.Context context=new ContextThemeWrapper(RuntimeEnvironment.getApplication(),R.style.Theme_PolishFighters);
  View root=LayoutInflater.from(context).inflate(R.layout.activity_game_bootstrap,null);
  render(root,"loading");
  ((TextView)root.findViewById(R.id.pf_loading_title)).setText(R.string.pf_error_title);
  ((TextView)root.findViewById(R.id.pf_status)).setText("Przykładowy komunikat błędu");
  ((TextView)root.findViewById(R.id.pf_loading_note)).setText(R.string.pf_error_help);
  root.findViewById(R.id.pf_progress).setVisibility(View.GONE);root.findViewById(R.id.pf_loading_percent).setVisibility(View.GONE);
  root.findViewById(R.id.pf_retry).setVisibility(View.VISIBLE);root.findViewById(R.id.pf_updates).setVisibility(View.VISIBLE);
  render(root,"error");assertTrue(root.findViewById(R.id.pf_retry).getHeight()>=56);
 }
}
