import javax.servlet.http.HttpServletResponse;

public class CorsFilterStrict {
  public void apply(HttpServletResponse resp) {
    resp.setHeader("Access-Control-Allow-Origin", "https://app.example.com");
  }
}
