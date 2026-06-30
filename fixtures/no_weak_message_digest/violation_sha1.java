import java.security.MessageDigest;

public class Hasher {
  public byte[] digest(byte[] data) throws Exception {
    MessageDigest md = MessageDigest.getInstance("SHA-1");
    return md.digest(data);
  }
}
