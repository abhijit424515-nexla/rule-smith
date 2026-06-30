package examples;

import java.util.List;
import java.util.concurrent.Future;
import java.util.concurrent.locks.ReentrantLock;
import javax.annotation.concurrent.GuardedBy;

// The same five defects, repaired. RuleSmith reports zero for the power-five.
public class PaymentGateway {

  private final ReentrantLock lock = new ReentrantLock();

  @GuardedBy("lock")
  private int balance;

  // (1) all setters run before the terminal build()
  Receipt issue(String customer) {
    Receipt.Builder b = Receipt.builder();
    b.customer(customer);
    b.total(100);
    return b.build();
  }

  // (2) pure method computes a value with no mutation at all
  @Pure
  int collectedCount(List<String> in) {
    return in.size() + 1;
  }

  // (3) guarded field read under its lock
  int currentBalance() {
    lock.lock();
    try {
      return balance;
    } finally {
      lock.unlock();
    }
  }

  // (4) resolve the Future outside the monitor
  String awaitSettlement(Future<String> task) throws Exception {
    return task.get();
  }

  // (5) no captured mutable state — fold over the input
  int sum(int[] amounts) {
    int acc = 0;
    for (int a : amounts) {
      acc += a;
    }
    return acc;
  }
}
