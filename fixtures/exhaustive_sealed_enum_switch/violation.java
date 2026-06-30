class Router {
  enum Mode {
    READ,
    WRITE,
    ADMIN
  }

  String label(Mode m) {
    switch (m) {
      case READ:
        return "r";
      case WRITE:
        return "w";
    }
    return "?";
  }
}
