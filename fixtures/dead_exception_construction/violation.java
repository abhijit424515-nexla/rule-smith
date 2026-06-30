class DeadThrowViolation {
  void process() {
    new IllegalStateException("bad state");
  }
}
