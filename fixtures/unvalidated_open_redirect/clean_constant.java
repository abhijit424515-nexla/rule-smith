import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class HomeServlet {
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws Exception {
    response.sendRedirect("/dashboard");
  }
}
