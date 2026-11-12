package org.libsdl.app;

import static org.junit.Assert.*;
import android.Manifest;
import android.bluetooth.*;
import android.content.Context;
import android.os.Build;
import android.view.InputDevice;
import java.util.*;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.shadows.ShadowBluetoothDevice;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 34}, shadows = {SDLAndroidCompatTest.GattShadow.class,
    SDLAndroidCompatTest.DeviceShadow.class, SDLAndroidCompatTest.ManagerShadow.class})
public class SDLAndroidCompatTest {
    private BluetoothGatt gatt;
    private GattShadow gattShadow;
    private BluetoothDevice device;
    private DeviceShadow deviceShadow;
    private BluetoothGattCharacteristic characteristic;
    private BluetoothGattDescriptor descriptor;

    @Before public void setup() {
        gatt = Shadow.newInstanceOf(BluetoothGatt.class);
        gattShadow = Shadow.extract(gatt);
        device = ShadowBluetoothDevice.newInstance("00:11:22:33:44:55");
        deviceShadow = Shadow.extract(device);
        characteristic = new BluetoothGattCharacteristic(UUID.randomUUID(), 0, 0);
        descriptor = new BluetoothGattDescriptor(UUID.randomUUID(), 0);
        if (Build.VERSION.SDK_INT >= 31) {
            Shadows.shadowOf(RuntimeEnvironment.getApplication()).grantPermissions(Manifest.permission.BLUETOOTH_CONNECT);
        }
    }

    @Test public void revokedPermissionFailsGattOperationsWithoutCrashing() {
        assertFalse(SDLAndroidCompat.readCharacteristic(gatt, characteristic));
        assertFalse(SDLAndroidCompat.writeCharacteristic(gatt, characteristic));
        assertFalse(SDLAndroidCompat.setCharacteristicNotification(gatt, characteristic, true));
        assertFalse(SDLAndroidCompat.writeDescriptor(gatt, descriptor));
        assertFalse(SDLAndroidCompat.discoverServices(gatt));
        assertFalse(SDLAndroidCompat.requestMtu(gatt, 517));
        assertEquals(6, gattShadow.calls.size());
    }

    @Test public void allowedGattOperationsRetainTheirResults() {
        gattShadow.denied = false;
        assertTrue(SDLAndroidCompat.readCharacteristic(gatt, characteristic));
        assertTrue(SDLAndroidCompat.writeCharacteristic(gatt, characteristic));
        assertTrue(SDLAndroidCompat.setCharacteristicNotification(gatt, characteristic, true));
        assertTrue(SDLAndroidCompat.writeDescriptor(gatt, descriptor));
        assertTrue(SDLAndroidCompat.discoverServices(gatt));
        assertTrue(SDLAndroidCompat.requestMtu(gatt, 517));
    }

    @Test public void cleanupStillAttemptsCloseAfterDeniedDisconnect() {
        SDLAndroidCompat.disconnect(gatt);
        SDLAndroidCompat.close(gatt);
        assertEquals(Arrays.asList("disconnect", "close"), gattShadow.calls);
        SDLAndroidCompat.disconnect(null);
        SDLAndroidCompat.close(null);
    }

    @Test public void revokedDeviceMetadataDoesNotIdentifyAController() {
        assertEquals("", SDLAndroidCompat.getName(device));
        assertEquals(BluetoothDevice.DEVICE_TYPE_UNKNOWN, SDLAndroidCompat.getType(device));
        deviceShadow.denied = false;
        assertEquals("SteamController", SDLAndroidCompat.getName(device));
        assertEquals(BluetoothDevice.DEVICE_TYPE_LE, SDLAndroidCompat.getType(device));
    }

    @Test public void revokedManagerReturnsDisconnectedAndEmptyDevices() {
        BluetoothManager manager = Shadow.newInstanceOf(BluetoothManager.class);
        assertEquals(BluetoothProfile.STATE_DISCONNECTED,
            SDLAndroidCompat.getConnectionState(manager, device, BluetoothProfile.GATT));
        assertTrue(SDLAndroidCompat.getConnectedDevices(manager, BluetoothProfile.GATT).isEmpty());
    }

    @Test public void revokedConnectDoesNotEscapeAsSecurityException() {
        Context context = RuntimeEnvironment.getApplication();
        assertNull(SDLAndroidCompat.connectGatt(device, context, false, new BluetoothGattCallback() {}));
        assertNull(SDLAndroidCompat.connectGatt(device, context, false, new BluetoothGattCallback() {}, 2));
        assertEquals(2, deviceShadow.connectCalls);
    }

    @Test @Config(sdk = 34) public void deniedPermissionPreventsConnectAttempt() {
        Shadows.shadowOf(RuntimeEnvironment.getApplication()).denyPermissions(Manifest.permission.BLUETOOTH_CONNECT);
        assertNull(SDLAndroidCompat.connectGatt(device, RuntimeEnvironment.getApplication(), false, new BluetoothGattCallback() {}));
        assertEquals(0, deviceShadow.connectCalls);
    }

    @Test public void unavailableGattAndCharacteristicsFailSafely() {
        assertFalse(SDLAndroidCompat.readCharacteristic(null, characteristic));
        assertFalse(SDLAndroidCompat.readCharacteristic(gatt, null));
        assertFalse(SDLAndroidCompat.writeCharacteristic(null, characteristic));
        assertFalse(SDLAndroidCompat.setCharacteristicNotification(gatt, null, true));
        assertFalse(SDLAndroidCompat.writeDescriptor(null, descriptor));
    }

    @Test @Config(sdk = 28) public void legacyPenDetectionDoesNotCallApi29() {
        InputDevice pen = Shadow.newInstanceOf(InputDevice.class);
        assertEquals(0, new SDLGenericMotionListener_API29().getPenDeviceType(pen));
    }

    @Implements(BluetoothGatt.class)
    public static class GattShadow {
        boolean denied = true;
        final List<String> calls = new ArrayList<>();
        private boolean access(String name) {
            calls.add(name);
            if (denied) throw new SecurityException("permission revoked after initialization");
            return true;
        }
        @Implementation protected boolean readCharacteristic(BluetoothGattCharacteristic value) { return access("read"); }
        @Implementation protected boolean writeCharacteristic(BluetoothGattCharacteristic value) { return access("write"); }
        @Implementation protected boolean setCharacteristicNotification(BluetoothGattCharacteristic value, boolean enabled) { return access("notify"); }
        @Implementation protected boolean writeDescriptor(BluetoothGattDescriptor value) { return access("descriptor"); }
        @Implementation protected boolean discoverServices() { return access("discover"); }
        @Implementation protected boolean requestMtu(int mtu) { return access("mtu"); }
        @Implementation protected void disconnect() { access("disconnect"); }
        @Implementation protected void close() { access("close"); }
    }

    @Implements(BluetoothDevice.class)
    public static class DeviceShadow {
        boolean denied = true;
        int connectCalls;
        @Implementation protected String getName() {
            if (denied) throw new SecurityException("metadata permission revoked");
            return "SteamController";
        }
        @Implementation protected int getType() {
            if (denied) throw new SecurityException("metadata permission revoked");
            return BluetoothDevice.DEVICE_TYPE_LE;
        }
        @Implementation protected BluetoothGatt connectGatt(Context context, boolean managed, BluetoothGattCallback callback) {
            connectCalls++;
            if (denied) throw new SecurityException("connection permission revoked");
            return Shadow.newInstanceOf(BluetoothGatt.class);
        }
        @Implementation protected BluetoothGatt connectGatt(Context context, boolean managed, BluetoothGattCallback callback, int transport) {
            return connectGatt(context, managed, callback);
        }
    }

    @Implements(BluetoothManager.class)
    public static class ManagerShadow {
        @Implementation protected int getConnectionState(BluetoothDevice device, int profile) { throw new SecurityException("manager permission revoked"); }
        @Implementation protected List<BluetoothDevice> getConnectedDevices(int profile) { throw new SecurityException("manager permission revoked"); }
    }
}
