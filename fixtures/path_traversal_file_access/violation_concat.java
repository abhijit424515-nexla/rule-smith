import java.io.FileInputStream;
import javax.servlet.http.HttpServletRequest;

public class Download {
  public void read(HttpServletRequest request) throws Exception {
    String name = request.getParameter("file");
    FileInputStream in = new FileInputStream("/var/data/" + name);
    in.close();
  }
}
