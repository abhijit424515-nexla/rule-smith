package examples;

import java.util.List;
import java.util.concurrent.Future;
import java.util.concurrent.locks.ReentrantLock;
import javax.annotation.concurrent.GuardedBy;

// Five defects that standard linters (SonarQube/PMD) do not flag — typestate,
// purity, lock-dominance, deadlock risk, and closure capture. Each needs real
// flow/semantic reasoning, not a syntax pattern.
public class PaymentGateway {

  private final ReentrantLock lock = new ReentrantLock();

  @GuardedBy("lock")
  private int balance;

  // (1) builder-terminal-before-setters — typestate: setter runs AFTER build()
  Receipt issue(String customer) {
    Receipt.Builder b = Receipt.builder();
    b.customer(customer);
    Receipt r = b.build();
    b.total(100); // <-- mutating a builder already finalized by build()
    return r;
  }

  // (2) pure-method-no-side-effects — @Pure method mutates its argument
  @Pure
  void collect(List<String> out) {
    out.add("entry"); // side effect in a method declared pure
  }

  // (3) guarded-by-lock-held — @GuardedBy field read without holding the lock
  int currentBalance() {
    return balance; // no lock acquired
  }

  // (4) blocking-call-while-holding-lock — Future.get() inside synchronized
  synchronized String awaitSettlement(Future<String> task) throws Exception {
    Future<String> fut = task;
    return fut.get(); // blocks the monitor; classic deadlock setup
  }

  // (5) lambda-captures-mutable-state — closure mutates captured array
  int sum(int[] amounts) {
    int[] acc = new int[1];
    Runnable r = () -> acc[0] += amounts.length;
    r.run();
    return acc[0];
  }
}
