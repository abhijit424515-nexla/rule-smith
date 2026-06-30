public class CleanLambda {
  int compute() {
    try {
      return 1;
    } finally {
      Runnable r =
          () -> {
            return;
          };
      r.run();
    }
  }
}
