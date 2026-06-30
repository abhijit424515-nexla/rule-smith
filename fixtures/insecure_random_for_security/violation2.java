import java.util.Random;

public class KeyGen {
  byte[] generateKey() {
    Random r = new Random();
    byte[] buf = new byte[16];
    r.nextBytes(buf);
    return buf;
  }
}
