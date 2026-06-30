import java.util.concurrent.atomic.AtomicInteger;

public class Counter {
  private final AtomicInteger count = new AtomicInteger();

  public void bump() {
    count.set(count.get() + 1);
  }
}
