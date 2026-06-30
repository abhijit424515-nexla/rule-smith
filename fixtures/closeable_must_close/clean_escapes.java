import java.io.FileInputStream;

public class SafeEscapes {
  public FileInputStream open(String path) throws Exception {
    FileInputStream in = new FileInputStream(path);
    return in;
  }
}
