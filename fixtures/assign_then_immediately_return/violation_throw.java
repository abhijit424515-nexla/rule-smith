class ThrowTemp {
  void g(boolean bad) {
    if (bad) {
      RuntimeException e = new RuntimeException("bad");
      throw e;
    }
  }
}
