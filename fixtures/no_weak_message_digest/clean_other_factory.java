import javax.crypto.KeyGenerator;

public class KeyMaker {
  public KeyGenerator make() throws Exception {
    return KeyGenerator.getInstance("MD5");
  }
}
