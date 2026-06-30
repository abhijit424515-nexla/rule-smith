import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.impl.client.HttpClientBuilder;

public class Violation {
  void configure(HttpClientBuilder b) {
    b.setSSLHostnameVerifier(NoopHostnameVerifier.INSTANCE);
  }
}
