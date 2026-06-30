public class Counter {
  private Object lock = new Object();
  private int n;

  public void inc() {
    synchronized (lock) {
      n++;
    }
  }
}
