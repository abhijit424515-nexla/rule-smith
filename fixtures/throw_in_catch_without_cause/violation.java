public class V1 {
  void run() {
    try {
      read();
    } catch (java.io.IOException e) {
      throw new RuntimeException("read failed");
    }
  }

  void read() throws java.io.IOException {}
}
