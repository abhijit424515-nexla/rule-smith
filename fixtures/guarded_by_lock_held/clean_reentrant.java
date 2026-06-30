import java.util.concurrent.locks.ReentrantLock;
import javax.annotation.concurrent.GuardedBy;

class Cache {
  private final ReentrantLock lock = new ReentrantLock();

  @GuardedBy("lock")
  private int value;

  int read() {
    lock.lock();
    try {
      return value;
    } finally {
      lock.unlock();
    }
  }
}
