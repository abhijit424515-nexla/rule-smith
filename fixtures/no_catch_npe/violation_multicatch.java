class B {
  void m(String s) {
    try {
      s.length();
    } catch (IllegalStateException | NullPointerException e) {
      handle(e);
    }
  }
  void handle(Exception e) {}
}
