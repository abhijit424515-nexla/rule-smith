class AfterThrow {
  void fail() {
    throw new RuntimeException("boom");
    int leftover = 1;
  }
}
