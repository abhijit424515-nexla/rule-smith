import java.util.Arrays;
import java.util.List;
import javax.servlet.http.HttpServletRequest;

public class SafeRunner {
  void run(HttpServletRequest request) throws Exception {
    String cmd = request.getParameter("cmd");
    List<String> allowed = Arrays.asList("ls", "pwd");
    if (!allowed.contains(cmd)) {
      return;
    }
    Runtime.getRuntime().exec(cmd);
  }
}
