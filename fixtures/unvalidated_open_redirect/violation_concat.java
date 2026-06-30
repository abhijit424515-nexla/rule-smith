import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class RedirectConcatServlet {
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws Exception {
    response.sendRedirect("/go?to=" + request.getParameter("dest"));
  }
}
