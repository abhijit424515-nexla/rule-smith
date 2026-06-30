import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;

public class LoginServlet {
  void issue(HttpServletResponse resp) {
    Cookie session = new Cookie("SESSIONID", "abc123");
    resp.addCookie(session);
  }
}
