public class ViolationCommentOnly {
  void run() {
    try {
      doWork();
    } catch (RuntimeException e) {
      handle(e);
    } finally {
      // nothing to clean up
    }
  }

  void doWork() {}

  void handle(RuntimeException e) {}
}
