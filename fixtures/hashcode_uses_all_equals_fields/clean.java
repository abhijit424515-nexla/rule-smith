import java.util.Objects;

public class Point {
  private int x;
  private int y;

  @Override
  public boolean equals(Object o) {
    if (!(o instanceof Point)) return false;
    Point p = (Point) o;
    return x == p.x && y == p.y;
  }

  @Override
  public int hashCode() {
    return Objects.hash(x, y);
  }
}
