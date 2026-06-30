class B {
  int parse(String s) {
    try {
      return Integer.parseInt(s);
    } catch (Throwable t) {
      return -1;
    }
  }
}
