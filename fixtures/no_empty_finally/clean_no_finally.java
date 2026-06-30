public class CleanNoFinally {
  void run() {
    try {
      doWork();
    } catch (RuntimeException e) {
      handle(e);
    }
  }

  void doWork() {}

  void handle(RuntimeException e) {}
}
