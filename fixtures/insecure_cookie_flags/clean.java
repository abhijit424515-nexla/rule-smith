import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;

public class SecureServlet {
  void issue(HttpServletResponse resp) {
    Cookie session = new Cookie("SESSIONID", "abc123");
    session.setSecure(true);
    session.setHttpOnly(true);
    resp.addCookie(session);
  }
}
