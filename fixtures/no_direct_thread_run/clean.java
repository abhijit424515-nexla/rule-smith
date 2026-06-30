public class Clean {
  void launch(Runnable task) {
    Thread t = new Thread(task);
    t.start();
  }
}
