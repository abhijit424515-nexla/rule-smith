import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class SanitizedHeader {
  void handle(HttpServletRequest req, HttpServletResponse resp) {
    String lang = req.getParameter("lang");
    resp.setHeader("X-Lang", lang.replaceAll("[\\r\\n]", ""));
  }
}
