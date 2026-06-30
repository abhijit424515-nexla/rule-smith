class Counter {
  private volatile int count;

  void inc() {
    count++;
  }

  void addBytes(int n) {
    count += n;
  }
}
