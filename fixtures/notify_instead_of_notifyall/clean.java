public class BoundedQueue {
  private final Object[] items = new Object[16];
  private int count;

  public synchronized void put(Object x) throws InterruptedException {
    while (count == items.length) {
      wait();
    }
    items[count++] = x;
    notifyAll();
  }
}
