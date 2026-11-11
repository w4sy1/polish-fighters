package io.github.openlf2.openlf2;

import android.annotation.SuppressLint;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import java.io.Closeable;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.UUID;

/** A two-phone RFCOMM link carries the engine's existing TCP protocol unchanged. */
@SuppressLint("MissingPermission") // Lobby checks CONNECT before creating a session.
public final class BluetoothSession implements Closeable {
    private static final UUID SERVICE = UUID.fromString("15821d89-466c-4580-bcab-a481d318a322");
    public interface Listener { void ready(String role, int port); void failed(String message); }
    private static BluetoothSession current;
    private volatile boolean closed;
    private BluetoothServerSocket listener;
    private BluetoothSocket bluetooth;
    private ServerSocket localListener;
    private Socket local;
    private StreamRelay relay;

    public static synchronized BluetoothSession create() {
        closeCurrent(); current = new BluetoothSession(); return current;
    }
    public static synchronized void closeCurrent() {
        if (current != null) current.close();
        current = null;
    }
    public void start(BluetoothAdapter adapter, BluetoothDevice peer, Listener callback) {
        Thread thread = new Thread(() -> {
            try {
                if (peer == null) {
                    synchronized (this) {
                        ensureOpen();
                        listener = adapter.listenUsingRfcommWithServiceRecord("Polish Fighters", SERVICE);
                    }
                    BluetoothSocket accepted = listener.accept();
                    synchronized (this) {
                        if (closed) { accepted.close(); return; }
                        bluetooth = accepted;
                        listener.close(); listener = null;
                    }
                    final int port;
                    try (ServerSocket reservation = new ServerSocket(0, 1, loopback())) {
                        port = reservation.getLocalPort();
                    }
                    callback.ready("host", port);
                    // SDL loads the mods before opening its listener; wait without blocking UI.
                    long deadline = System.nanoTime() + 120_000_000_000L;
                    while (!closed && System.nanoTime() < deadline) {
                        Socket attempt = new Socket();
                        synchronized (this) { ensureOpen(); local = attempt; }
                        try { attempt.connect(new InetSocketAddress(loopback(), port), 500); break; }
                        catch (IOException waiting) { attempt.close(); Thread.sleep(100); }
                    }
                    ensureOpen();
                    if (local == null || !local.isConnected()) throw new IOException("Gra nie uruchomiła połączenia na czas.");
                } else {
                    synchronized (this) {
                        ensureOpen(); bluetooth = peer.createRfcommSocketToServiceRecord(SERVICE);
                    }
                    bluetooth.connect();
                    synchronized (this) {
                        ensureOpen(); localListener = new ServerSocket(0, 1, loopback());
                    }
                    callback.ready("join", localListener.getLocalPort());
                    localListener.setSoTimeout(120000);
                    Socket accepted = localListener.accept();
                    synchronized (this) {
                        if (closed) { accepted.close(); return; }
                        local = accepted; localListener.close(); localListener = null;
                    }
                }
                synchronized (this) {
                    ensureOpen(); local.setTcpNoDelay(true); relay = new StreamRelay(local, bluetooth);
                }
                relay.run(local.getInputStream(), local.getOutputStream(),
                    bluetooth.getInputStream(), bluetooth.getOutputStream());
                if (!closed) callback.failed("Połączenie Bluetooth zostało zakończone.");
            } catch (IOException | InterruptedException | SecurityException error) {
                if (!closed) callback.failed("Bluetooth: " + error.getMessage());
            } finally { close(); }
        }, "PF-Bluetooth");
        thread.setDaemon(true); thread.start();
    }
    private static InetAddress loopback() throws IOException { return InetAddress.getByName("127.0.0.1"); }
    private void ensureOpen() throws IOException { if (closed) throw new IOException("Anulowano połączenie."); }
    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        if (relay != null) relay.close();
        try { if (listener != null) listener.close(); } catch (IOException ignored) { }
        try { if (bluetooth != null) bluetooth.close(); } catch (IOException ignored) { }
        try { if (localListener != null) localListener.close(); } catch (IOException ignored) { }
        try { if (local != null) local.close(); } catch (IOException ignored) { }
    }
}
