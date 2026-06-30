public class C1 {
  void run() {
    try {
      read();
    } catch (java.io.IOException e) {
      throw new RuntimeException("read failed", e);
    }
  }

  void read() throws java.io.IOException {}
}
