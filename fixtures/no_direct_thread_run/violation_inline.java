public class ViolationInline {
  void launch(Runnable task) {
    new Thread(task).run();
  }
}
