import java.io.IOException;

class E {
  void load() {
    try {
      doWork();
    } catch (IOException | IllegalStateException e) {
      handle(e);
    }
  }

  void doWork() throws IOException {}

  void handle(Exception e) {}
}
