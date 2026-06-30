public class Parser {
  static class StopSignal extends RuntimeException {}

  int findFirst(int[] xs, int target) {
    try {
      for (int i = 0; i < xs.length; i++) {
        if (xs[i] == target) {
          throw new StopSignal();
        }
      }
    } catch (StopSignal s) {
      return 1;
    }
    return -1;
  }
}
