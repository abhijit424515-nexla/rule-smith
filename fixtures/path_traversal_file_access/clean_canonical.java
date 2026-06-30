import java.io.File;
import java.io.FileInputStream;
import javax.servlet.http.HttpServletRequest;

public class SafeDownload {
  public void read(HttpServletRequest request) throws Exception {
    String name = request.getParameter("file");
    File base = new File("/var/data");
    File f = new File(base, name).getCanonicalFile();
    if (!f.getCanonicalPath().startsWith(base.getCanonicalPath())) {
      throw new SecurityException("path traversal");
    }
    FileInputStream in = new FileInputStream(f);
    in.close();
  }
}
