import javax.annotation.concurrent.Immutable;

@Immutable
public final class Point {
  private final int x;
  private final String label;

  Point(int x, String label) {
    this.x = x;
    this.label = label;
  }

  int x() {
    return x;
  }

  String label() {
    return label;
  }
}
