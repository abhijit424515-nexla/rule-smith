public class Counter {
  private int n;

  public void inc() {
    synchronized (this) {
      n++;
    }
  }
}
