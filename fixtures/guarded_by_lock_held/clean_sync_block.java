import javax.annotation.concurrent.GuardedBy;

class Store {
  private final Object mutex = new Object();

  @GuardedBy("mutex")
  private int total;

  void add(int n) {
    synchronized (mutex) {
      total += n;
    }
  }
}
