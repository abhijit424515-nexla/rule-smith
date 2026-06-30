public class Violation {
  void launch(Runnable task) {
    Thread t = new Thread(task);
    t.run();
  }
}
