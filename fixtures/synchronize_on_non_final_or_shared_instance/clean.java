public class Counter {
  private final Object lock = new Object();
  private int n;

  public void inc() {
    synchronized (lock) {
      n++;
    }
  }
}
