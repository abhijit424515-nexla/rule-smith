import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.SSLSession;

public class Violation2 {
  HostnameVerifier hv =
      new HostnameVerifier() {
        public boolean verify(String hostname, SSLSession session) {
          return true;
        }
      };
}
