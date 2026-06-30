class Router {
  String route(int code) {
    switch (code) {
      case 1:
      case 2:
        return "low";
      case 3:
        System.out.println("three");
        break;
      default:
        return "other";
    }
    return "done";
  }
}
