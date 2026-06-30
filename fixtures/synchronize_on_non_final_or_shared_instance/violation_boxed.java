public class Cache {
  private final Integer lock = 0;
  private int n;

  public void inc() {
    synchronized (lock) {
      n++;
    }
  }
}
