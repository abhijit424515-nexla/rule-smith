class ViolationNotFalse {
  void run(boolean done) {
    while (done != false) {
      done = stop();
    }
  }

  boolean stop() {
    return true;
  }
}
