package demo;

import javax.net.ssl.SSLContext;

public class StrongClient {
  public SSLContext build() throws Exception {
    SSLContext ctx = SSLContext.getInstance("TLSv1.3");
    return ctx;
  }
}
