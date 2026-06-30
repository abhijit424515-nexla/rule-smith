package demo;

import javax.crypto.Cipher;

public class Weak {
  public Cipher make() throws Exception {
    return Cipher.getInstance("DES");
  }
}
