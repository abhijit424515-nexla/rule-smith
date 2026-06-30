public class V2 {
  void run() {
    try {
      query();
    } catch (java.sql.SQLException e) {
      throw new IllegalStateException(e.getMessage());
    }
  }

  void query() throws java.sql.SQLException {}
}
