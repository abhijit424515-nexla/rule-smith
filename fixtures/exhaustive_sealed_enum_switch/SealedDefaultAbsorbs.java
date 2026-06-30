class Painter {
  sealed interface Shape permits Circle, Square {}

  static final class Circle implements Shape {}

  static final class Square implements Shape {}

  int area(Shape s) {
    return switch (s) {
      case Circle c -> 1;
      case Square sq -> 2;
      default -> 0;
    };
  }
}
