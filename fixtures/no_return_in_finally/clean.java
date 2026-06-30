public class Clean {
  int compute() {
    try {
      return 1;
    } finally {
      cleanup();
    }
  }

  void cleanup() {}
}
