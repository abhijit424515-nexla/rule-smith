class D {
  void k() {
    try {
      risky();
    } catch (IllegalArgumentException | IllegalStateException e) {
      log(e);
    }
  }
}
