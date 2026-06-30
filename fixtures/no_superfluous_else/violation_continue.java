public class B {
  void run(int[] xs) {
    for (int x : xs) {
      if (x < 0) {
        continue;
      } else {
        process(x);
      }
    }
  }

  void process(int x) {}
}
