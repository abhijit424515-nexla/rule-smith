public class Worker {
  private final Object lock = new Object();

  void go() throws InterruptedException {
    synchronized (lock) {
      lock.wait();
    }
  }
}
