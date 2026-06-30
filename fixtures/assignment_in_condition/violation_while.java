class C {
  boolean running;

  void m() {
    while (running = true) {
      step();
    }
  }

  void step() {}
}
