public class C2 {
  void run() {
    try {
      query();
    } catch (java.sql.SQLException e) {
      IllegalStateException ex = new IllegalStateException("bad");
      ex.initCause(e);
      throw ex;
    }
  }

  void query() throws java.sql.SQLException {}
}
