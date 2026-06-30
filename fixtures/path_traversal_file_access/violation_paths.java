import java.io.File;
import javax.servlet.http.HttpServletRequest;

public class Open {
  public File locate(HttpServletRequest request) {
    String p = request.getHeader("X-Path");
    return new File(p);
  }
}
