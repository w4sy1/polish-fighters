// SPDX-License-Identifier: MIT
package org.libsdl.app;

import android.Manifest;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;
import java.util.Collections;
import java.util.List;

/** Permission can be revoked after HID initialization, including during a GATT callback. */
final class SDLAndroidCompat {
    private SDLAndroidCompat() {}

    private static void denied(String operation, SecurityException error) {
        Log.w("hidapi", "Bluetooth permission denied during " + operation, error);
    }

    private static boolean canConnect(Context context) {
        return context != null && (Build.VERSION.SDK_INT < 31 ||
            context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED);
    }

    static boolean readCharacteristic(BluetoothGatt gatt, BluetoothGattCharacteristic value) {
        if (gatt == null || value == null) return false;
        try { return gatt.readCharacteristic(value); }
        catch (SecurityException error) { denied("readCharacteristic", error); return false; }
    }

    static boolean writeCharacteristic(BluetoothGatt gatt, BluetoothGattCharacteristic value) {
        if (gatt == null || value == null) return false;
        try { return gatt.writeCharacteristic(value); }
        catch (SecurityException error) { denied("writeCharacteristic", error); return false; }
    }

    static boolean setCharacteristicNotification(BluetoothGatt gatt, BluetoothGattCharacteristic value, boolean enabled) {
        if (gatt == null || value == null) return false;
        try { return gatt.setCharacteristicNotification(value, enabled); }
        catch (SecurityException error) { denied("setCharacteristicNotification", error); return false; }
    }

    static boolean writeDescriptor(BluetoothGatt gatt, BluetoothGattDescriptor value) {
        if (gatt == null || value == null) return false;
        try { return gatt.writeDescriptor(value); }
        catch (SecurityException error) { denied("writeDescriptor", error); return false; }
    }

    static BluetoothGatt connectGatt(BluetoothDevice device, Context context, boolean managed, BluetoothGattCallback callback) {
        if (device == null || !canConnect(context)) return null;
        try { return device.connectGatt(context, managed, callback); }
        catch (SecurityException error) { denied("connectGatt", error); return null; }
    }

    static BluetoothGatt connectGatt(BluetoothDevice device, Context context, boolean managed, BluetoothGattCallback callback, int transport) {
        if (device == null || !canConnect(context)) return null;
        if (Build.VERSION.SDK_INT < 23) return connectGatt(device, context, managed, callback);
        try { return device.connectGatt(context, managed, callback, transport); }
        catch (SecurityException error) { denied("connectGatt", error); return null; }
    }

    static int getConnectionState(BluetoothManager manager, BluetoothDevice device, int profile) {
        if (manager == null || device == null) return BluetoothProfile.STATE_DISCONNECTED;
        try { return manager.getConnectionState(device, profile); }
        catch (SecurityException error) { denied("getConnectionState", error); return BluetoothProfile.STATE_DISCONNECTED; }
    }

    static List<BluetoothDevice> getConnectedDevices(BluetoothManager manager, int profile) {
        if (manager == null) return Collections.emptyList();
        try { return manager.getConnectedDevices(profile); }
        catch (SecurityException error) { denied("getConnectedDevices", error); return Collections.emptyList(); }
    }

    static void disconnect(BluetoothGatt gatt) {
        if (gatt == null) return;
        try { gatt.disconnect(); }
        catch (SecurityException error) { denied("disconnect", error); }
    }

    static void close(BluetoothGatt gatt) {
        if (gatt == null) return;
        try { gatt.close(); }
        catch (SecurityException error) { denied("close", error); }
    }

    static boolean discoverServices(BluetoothGatt gatt) {
        if (gatt == null) return false;
        try { return gatt.discoverServices(); }
        catch (SecurityException error) { denied("discoverServices", error); return false; }
    }

    static boolean requestMtu(BluetoothGatt gatt, int mtu) {
        if (gatt == null) return false;
        try { return gatt.requestMtu(mtu); }
        catch (SecurityException error) { denied("requestMtu", error); return false; }
    }

    static String getName(BluetoothDevice device) {
        if (device == null) return "";
        try { String name = device.getName(); return name == null ? "" : name; }
        catch (SecurityException error) { denied("getName", error); return ""; }
    }

    static int getType(BluetoothDevice device) {
        if (device == null) return BluetoothDevice.DEVICE_TYPE_UNKNOWN;
        try { return device.getType(); }
        catch (SecurityException error) { denied("getType", error); return BluetoothDevice.DEVICE_TYPE_UNKNOWN; }
    }
}
