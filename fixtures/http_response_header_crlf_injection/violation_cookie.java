import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class CookieEcho {
  void handle(HttpServletRequest req, HttpServletResponse resp) {
    Cookie c = new Cookie("sid", req.getParameter("sid"));
    resp.addCookie(c);
  }
}
