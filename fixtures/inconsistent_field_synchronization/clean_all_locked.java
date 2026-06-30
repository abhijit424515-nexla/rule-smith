class Counter {
  private int count;

  synchronized int get() {
    return count;
  }

  synchronized void inc() {
    count++;
  }
}
