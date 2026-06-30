import javax.servlet.http.HttpServletResponse;

public class StaticHeader {
  void handle(HttpServletResponse resp) {
    resp.setHeader("Cache-Control", "no-cache");
  }
}
