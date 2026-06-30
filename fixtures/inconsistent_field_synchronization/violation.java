class Counter {
  private int count;

  synchronized int get() {
    return count;
  }

  void reset() {
    count = 0;
  }
}
