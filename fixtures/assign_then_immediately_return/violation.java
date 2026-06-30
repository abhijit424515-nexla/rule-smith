class ReturnTemp {
  int compute() {
    return 42;
  }

  int f() {
    int x = compute();
    return x;
  }
}
