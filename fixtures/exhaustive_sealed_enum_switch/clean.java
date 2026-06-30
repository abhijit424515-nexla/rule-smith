class Router {
  enum Mode {
    READ,
    WRITE,
    ADMIN
  }

  String label(Mode m) {
    return switch (m) {
      case READ -> "r";
      case WRITE -> "w";
      case ADMIN -> "a";
    };
  }
}
