class UsedTwice {
  int compute() {
    return 1;
  }

  void log(int v) {}

  int f() {
    int x = compute();
    log(x);
    return x;
  }
}
