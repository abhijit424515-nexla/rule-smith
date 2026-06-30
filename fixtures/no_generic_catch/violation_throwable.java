class B {
  void g() {
    try {
      risky();
    } catch (Throwable t) {
      log(t);
    }
  }
}
