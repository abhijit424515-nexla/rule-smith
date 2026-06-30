class Counter {
  private int count;

  void inc() {
    count++;
  }

  void add(int n) {
    int local = 0;
    local += n;
    count = count + local;
  }
}
