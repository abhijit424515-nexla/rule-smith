public class Registry {
  private final Object lock = new Object();
  private int n;

  public void inc() {
    synchronized (lock) {
      n++;
    }
  }

  public Class<?> kind() {
    return getClass();
  }
}
