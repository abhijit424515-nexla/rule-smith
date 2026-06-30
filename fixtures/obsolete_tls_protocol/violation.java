package demo;

import javax.net.ssl.SSLContext;

public class LegacyClient {
  public SSLContext build() throws Exception {
    return SSLContext.getInstance("SSLv3");
  }
}
