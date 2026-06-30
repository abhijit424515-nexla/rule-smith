import java.util.concurrent.atomic.AtomicInteger;

public class CleanCounter {
  private final AtomicInteger count = new AtomicInteger();

  public void bump() {
    count.incrementAndGet();
  }

  public boolean tryClaim(int expected) {
    return count.compareAndSet(expected, expected + 1);
  }
}
