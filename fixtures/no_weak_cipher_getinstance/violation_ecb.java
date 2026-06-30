package demo;

import javax.crypto.Cipher;

public class WeakMode {
  public Cipher make() throws Exception {
    return Cipher.getInstance("AES/ECB/PKCS5Padding");
  }
}
