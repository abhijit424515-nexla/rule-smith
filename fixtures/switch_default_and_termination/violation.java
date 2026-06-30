class Router {
  String route(int code) {
    switch (code) {
      case 1:
        System.out.println("one");
      case 2:
        return "two";
      default:
        return "other";
    }
  }
}
