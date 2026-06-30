import java.sql.Connection;
import java.sql.DriverManager;

public class LeakEarlyReturn {
  public void run(String url, boolean skip) throws Exception {
    Connection conn = DriverManager.getConnection(url);
    if (skip) {
      return;
    }
    conn.close();
  }
}
