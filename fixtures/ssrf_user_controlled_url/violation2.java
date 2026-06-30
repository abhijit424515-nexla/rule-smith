import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.springframework.web.bind.annotation.RequestParam;

public class Proxy {
  public String proxy(@RequestParam String host) throws Exception {
    HttpClient client = HttpClient.newHttpClient();
    HttpRequest req = HttpRequest.newBuilder().uri(URI.create(host)).build();
    HttpResponse<String> r = client.send(req, HttpResponse.BodyHandlers.ofString());
    return r.body();
  }
}
