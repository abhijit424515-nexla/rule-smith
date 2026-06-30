import javax.annotation.concurrent.Immutable;

@Immutable
public final class Counter {
  private int count;
  private final String name;

  Counter(String name) {
    this.name = name;
  }

  int count() {
    return count;
  }
}
