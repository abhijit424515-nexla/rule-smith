import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.SSLSession;

public class Clean {
  HostnameVerifier hv =
      new HostnameVerifier() {
        public boolean verify(String hostname, SSLSession session) {
          return hostname.equals(session.getPeerHost());
        }
      };
}
