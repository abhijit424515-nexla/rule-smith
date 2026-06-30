class GuardReturn {
  void run(int x) {
    if (x > 0) {
      return;
    }
    doStuff();
  }

  void doStuff() {}
}
