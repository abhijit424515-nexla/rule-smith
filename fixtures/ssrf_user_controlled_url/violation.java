import java.net.HttpURLConnection;
import java.net.URL;
import javax.servlet.http.HttpServletRequest;

public class Fetcher {
  public void fetch(HttpServletRequest request) throws Exception {
    String target = request.getParameter("url");
    URL u = new URL(target);
    HttpURLConnection c = (HttpURLConnection) u.openConnection();
    c.connect();
  }
}
