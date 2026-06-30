import java.util.concurrent.atomic.AtomicLong;

public class Totals {
  private final AtomicLong total = new AtomicLong();

  public void add(long delta) {
    long current = total.get();
    total.set(current + delta);
  }
}
