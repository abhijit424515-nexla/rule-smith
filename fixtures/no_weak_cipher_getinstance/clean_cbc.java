package demo;

import javax.crypto.Cipher;

public class StrongCbc {
  public Cipher make() throws Exception {
    return Cipher.getInstance("AES/CBC/PKCS5Padding");
  }
}
