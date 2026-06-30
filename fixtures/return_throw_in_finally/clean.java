class C1 {
  int read() {
    try {
      return compute();
    } finally {
      cleanup();
    }
  }

  void cleanup() {}

  int compute() {
    return 0;
  }
}
