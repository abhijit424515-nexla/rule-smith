import java.security.cert.X509Certificate;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

public class TrustFactory {
  public TrustManager build() {
    return new X509TrustManager() {
      public void checkServerTrusted(X509Certificate[] chain, String authType) {
        // trust everyone, no checks
      }

      public void checkClientTrusted(X509Certificate[] chain, String authType) {
        doRealCheck(chain);
      }

      public X509Certificate[] getAcceptedIssuers() {
        return new X509Certificate[0];
      }

      private void doRealCheck(X509Certificate[] chain) {}
    };
  }
}
