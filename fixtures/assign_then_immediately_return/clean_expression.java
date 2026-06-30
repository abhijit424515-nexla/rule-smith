class ReturnsExpr {
  int compute() {
    return 1;
  }

  int f() {
    int x = compute();
    return x + 1;
  }
}
