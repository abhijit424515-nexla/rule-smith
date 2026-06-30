public class C3 {
  void run() throws java.io.IOException {
    try {
      read();
    } catch (java.io.IOException e) {
      log(e);
      throw e;
    }
  }

  void read() throws java.io.IOException {}

  void log(Object o) {}
}
