class CleanCall {
  int value;

  void refresh() {
    value = compute();
  }

  int compute() {
    return 42;
  }
}
