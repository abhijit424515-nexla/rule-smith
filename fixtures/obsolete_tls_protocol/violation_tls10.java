package demo;

import javax.net.ssl.SSLContext;

public class OldTls {
  public SSLContext build() throws Exception {
    SSLContext ctx = SSLContext.getInstance("TLSv1.1");
    return ctx;
  }
}
