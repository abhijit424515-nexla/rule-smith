import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class AllowlistServlet {
  private static final Map<String, String> ALLOWED = Map.of("home", "/home", "help", "/help");

  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws Exception {
    String key = request.getParameter("page");
    String target = ALLOWED.getOrDefault(key, "/home");
    response.sendRedirect(target);
  }
}
