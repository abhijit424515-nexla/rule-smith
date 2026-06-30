import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

public class Cg {
  SecretKeySpec make() throws Exception {
    KeyGenerator kg = KeyGenerator.getInstance("AES");
    SecretKey sk = kg.generateKey();
    byte[] keyBytes = sk.getEncoded();
    return new SecretKeySpec(keyBytes, "AES");
  }
}
