import java.io.FileInputStream;

public class SafeTwr {
  public int firstByte(String path) throws Exception {
    try (FileInputStream in = new FileInputStream(path)) {
      return in.read();
    }
  }
}
