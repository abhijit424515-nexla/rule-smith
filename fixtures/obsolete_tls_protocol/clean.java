package demo;

import javax.net.ssl.SSLContext;

public class ModernClient {
  public SSLContext build() throws Exception {
    return SSLContext.getInstance("TLSv1.2");
  }
}
