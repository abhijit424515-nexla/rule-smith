class A {
  int f(int x) {
    int y = compute();
    if (x > 0) {
      return y + 1;
    }
    return 0;
  }

  int compute() {
    return 5;
  }
}
