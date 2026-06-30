import java.io.FileInputStream;

public class LeakNoClose {
  public void copy(String path) throws Exception {
    FileInputStream in = new FileInputStream(path);
    int b = in.read();
    System.out.println(b);
  }
}
