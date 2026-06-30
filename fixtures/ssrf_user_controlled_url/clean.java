import java.net.URL;

public class Clean1 {
  public void ping() throws Exception {
    URL u = new URL("https://api.internal.example.com/health");
    u.openConnection().connect();
  }
}
