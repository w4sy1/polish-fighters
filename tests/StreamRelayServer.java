import io.github.openlf2.openlf2.StreamRelay;
import java.net.*;
/** Test adapter: replaces only the RFCOMM wire with loopback TCP. */
public class StreamRelayServer {
    public static void main(String[] args) throws Exception {
        try(ServerSocket listener=new ServerSocket(0,1,InetAddress.getLoopbackAddress())) {
            System.out.println(listener.getLocalPort()); System.out.flush();
            listener.setSoTimeout(120000);
            try(Socket guest=listener.accept();
                Socket host=connect(Integer.parseInt(args[0]));
                StreamRelay relay=new StreamRelay(guest,host)) {
                guest.setTcpNoDelay(true);host.setTcpNoDelay(true);
                relay.run(guest.getInputStream(),guest.getOutputStream(),host.getInputStream(),host.getOutputStream());
            }
        }
    }
    private static Socket connect(int port) throws Exception {
        long deadline=System.nanoTime()+120_000_000_000L;
        while(System.nanoTime()<deadline) {
            Socket socket=new Socket();
            try {socket.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(),port),500);return socket;}
            catch(java.io.IOException waiting){socket.close();Thread.sleep(100);}
        }
        throw new java.io.IOException("native host did not open listener");
    }
}
