public class Point {
  final int x;
  final int y;

  Point(int x, int y) {
    this.x = x;
    this.y = y;
  }

  public boolean equals(Point other) {
    return other != null && x == other.x && y == other.y;
  }
}
