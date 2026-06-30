class Parser {
  int parse(int t) {
    switch (t) {
      case 1:
        System.out.println("setup");
      // fall through
      case 2:
        return 2;
      default:
        return 0;
    }
  }
}
