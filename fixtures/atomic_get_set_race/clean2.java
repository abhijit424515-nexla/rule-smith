import java.util.concurrent.atomic.AtomicInteger;

public class Independent {
  private final AtomicInteger a = new AtomicInteger();
  private final AtomicInteger b = new AtomicInteger();

  public void reset() {
    a.set(0);
  }

  public void copy() {
    b.set(a.get());
  }
}
