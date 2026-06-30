import javax.servlet.http.HttpServletResponse;

public class CorsFilterHeader {
  public void apply(HttpServletResponse resp) {
    resp.setHeader("Access-Control-Allow-Origin", "*");
    resp.setHeader("Access-Control-Allow-Credentials", "true");
  }
}
