import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;

class ConditionInWhile {
  private final Lock lock;
  private final Condition cond;
  private boolean ready;

  ConditionInWhile(Lock lock) {
    this.lock = lock;
    this.cond = lock.newCondition();
  }

  void awaitReady() throws InterruptedException {
    lock.lock();
    try {
      while (!ready) {
        cond.await();
      }
    } finally {
      lock.unlock();
    }
  }
}
