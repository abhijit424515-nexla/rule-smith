import java.io.FileInputStream;

public class SafeFinally {
  public int firstByte(String path) throws Exception {
    FileInputStream in = new FileInputStream(path);
    try {
      return in.read();
    } finally {
      in.close();
    }
  }
}
