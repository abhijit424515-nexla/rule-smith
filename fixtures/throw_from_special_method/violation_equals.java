public class Point {
  private final int x;
  private final int y;

  public Point(int x, int y) {
    this.x = x;
    this.y = y;
  }

  @Override
  public boolean equals(Object o) {
    if (o == null) {
      throw new NullPointerException("o is null");
    }
    if (!(o instanceof Point)) {
      throw new ClassCastException("not a Point");
    }
    Point p = (Point) o;
    return x == p.x && y == p.y;
  }
}
