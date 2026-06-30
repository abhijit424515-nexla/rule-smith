import java.io.File;
import java.io.FileInputStream;

public class Config {
  public void load() throws Exception {
    File f = new File("/etc/app/config.properties");
    FileInputStream in = new FileInputStream(f);
    in.close();
  }
}
