import java.util.concurrent.locks.ReentrantLock;

class Counter {
  private final ReentrantLock lock = new ReentrantLock();
  private volatile int count;

  void inc() {
    lock.lock();
    try {
      count++;
    } finally {
      lock.unlock();
    }
  }

  synchronized void add(int n) {
    count += n;
  }
}
