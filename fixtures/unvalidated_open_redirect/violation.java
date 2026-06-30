import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class RedirectServlet {
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws Exception {
    String url = request.getParameter("next");
    response.sendRedirect(url);
  }
}
