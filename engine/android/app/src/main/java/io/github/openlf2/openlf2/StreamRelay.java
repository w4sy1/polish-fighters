package io.github.openlf2.openlf2;

import java.io.Closeable;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.atomic.AtomicBoolean;

/** Full duplex byte relay. Closing either endpoint unblocks both pumps. */
public final class StreamRelay implements Closeable {
    private final Closeable first, second;
    private final AtomicBoolean closed = new AtomicBoolean();
    public StreamRelay(Closeable first, Closeable second) {
        this.first = first; this.second = second;
    }
    public void run(InputStream inA, OutputStream outA, InputStream inB, OutputStream outB)
            throws InterruptedException {
        Thread reverse = new Thread(() -> pump(inB, outA), "PF-relay-reverse");
        reverse.setDaemon(true);
        reverse.start();
        pump(inA, outB);
        reverse.join();
    }
    private void pump(InputStream input, OutputStream output) {
        byte[] bytes = new byte[8192];
        try {
            int count;
            while (!closed.get() && (count = input.read(bytes)) != -1) {
                output.write(bytes, 0, count);
                output.flush();
            }
        } catch (IOException ignored) {
            // EOF, remote disconnect and cancellation all close the other endpoint.
        } finally { close(); }
    }
    @Override public void close() {
        if (!closed.compareAndSet(false, true)) return;
        try { first.close(); } catch (IOException ignored) { }
        try { second.close(); } catch (IOException ignored) { }
    }
}
