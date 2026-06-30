import javax.servlet.http.HttpServletRequest;

public class CmdRunner {
  void run(HttpServletRequest request) throws Exception {
    String cmd = request.getParameter("cmd");
    Runtime.getRuntime().exec(cmd);
  }
}
