import java.security.MessageDigest;

public class Hasher {
  public byte[] digest(byte[] data) throws Exception {
    MessageDigest md = MessageDigest.getInstance("MD5");
    return md.digest(data);
  }
}
