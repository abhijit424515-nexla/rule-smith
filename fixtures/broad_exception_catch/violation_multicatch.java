import java.io.IOException;

class C {
  void load() {
    try {
      doWork();
    } catch (IOException | RuntimeException e) {
      handle(e);
    }
  }

  void doWork() throws IOException {}

  void handle(Exception e) {}
}
