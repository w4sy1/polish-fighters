import io.github.openlf2.openlf2.StreamRelay;
import java.net.*;
import java.util.Arrays;
import java.util.Random;
import java.util.concurrent.*;

/** Tests the production relay, without Android or a radio. */
public class StreamRelayTest {
    public static void main(String[] args) throws Exception {
        for (int round=0; round<3; round++) {
            try (ServerSocket leftServer=new ServerSocket(0,1,InetAddress.getLoopbackAddress());
                 ServerSocket rightServer=new ServerSocket(0,1,InetAddress.getLoopbackAddress());
                 Socket left=new Socket(InetAddress.getLoopbackAddress(),leftServer.getLocalPort());
                 Socket a=leftServer.accept();
                 Socket right=new Socket(InetAddress.getLoopbackAddress(),rightServer.getLocalPort());
                 Socket b=rightServer.accept()) {
                left.setSoTimeout(5000); right.setSoTimeout(5000);
                StreamRelay relay=new StreamRelay(a,b);
                Thread transport=new Thread(() -> {
                    try { relay.run(a.getInputStream(),a.getOutputStream(),b.getInputStream(),b.getOutputStream()); }
                    catch(Exception e) { throw new RuntimeException(e); }
                });
                transport.start();
                byte[] one=new byte[262144],two=new byte[262144];
                new Random(10+round).nextBytes(one);new Random(50+round).nextBytes(two);
                ExecutorService workers=Executors.newFixedThreadPool(2);
                try {
                    Future<?> writeOne=workers.submit(() -> {try {left.getOutputStream().write(one);}catch(Exception e){throw new RuntimeException(e);}});
                    Future<?> writeTwo=workers.submit(() -> {try {right.getOutputStream().write(two);}catch(Exception e){throw new RuntimeException(e);}});
                    if(!Arrays.equals(two,left.getInputStream().readNBytes(two.length))) throw new AssertionError("reverse corruption");
                    if(!Arrays.equals(one,right.getInputStream().readNBytes(one.length))) throw new AssertionError("forward corruption");
                    writeOne.get(5,TimeUnit.SECONDS);writeTwo.get(5,TimeUnit.SECONDS);
                    if(round==0) left.close(); else if(round==1) right.close(); else relay.close();
                    transport.join(3000);
                    if(transport.isAlive()) throw new AssertionError("disconnect did not unblock both pumps");
                    relay.close(); // cancellation must be idempotent
                } finally {relay.close();workers.shutdownNow();}
            }
        }
        System.out.println("PASS: production full duplex relay, 3 x 512 KiB, both remote disconnects and cancellation");
    }
}
