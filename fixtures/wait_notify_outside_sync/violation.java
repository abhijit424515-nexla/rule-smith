public class Worker {
  private final Object lock = new Object();

  void go() {
    lock.notify();
  }
}
