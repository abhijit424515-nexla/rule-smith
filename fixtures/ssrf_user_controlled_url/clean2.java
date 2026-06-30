import java.net.URI;
import java.net.http.HttpRequest;

public class Clean2 {
  private static final String BASE = "https://svc.internal/";

  public HttpRequest build(String pathSuffix) {
    URI uri = URI.create(BASE);
    return HttpRequest.newBuilder().uri(uri).build();
  }
}
