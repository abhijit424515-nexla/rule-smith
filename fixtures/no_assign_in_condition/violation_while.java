class B {
  void g(boolean done) {
    while (done = check()) {
      step();
    }
  }

  boolean check() {
    return false;
  }

  void step() {}
}
