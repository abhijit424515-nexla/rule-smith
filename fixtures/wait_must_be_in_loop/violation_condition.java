import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;

class ConditionOutsideLoop {
  private final Lock lock;
  private final Condition cond;
  private boolean ready;

  ConditionOutsideLoop(Lock lock) {
    this.lock = lock;
    this.cond = lock.newCondition();
  }

  void awaitReady() throws InterruptedException {
    lock.lock();
    try {
      if (!ready) {
        cond.await();
      }
    } finally {
      lock.unlock();
    }
  }
}
