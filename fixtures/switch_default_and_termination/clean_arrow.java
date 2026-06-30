class Mapper {
  String map(int x) {
    switch (x) {
      case 1 -> System.out.println("a");
      case 2 -> System.out.println("b");
      default -> System.out.println("z");
    }
    return "ok";
  }
}
