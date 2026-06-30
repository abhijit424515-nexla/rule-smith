package demo;

import javax.crypto.Cipher;

public class Strong {
  public Cipher make() throws Exception {
    return Cipher.getInstance("AES/GCM/NoPadding");
  }
}
