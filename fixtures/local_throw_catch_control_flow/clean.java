public class Validator {
  void check(int x) {
    if (x < 0) {
      throw new IllegalArgumentException("negative");
    }
  }
}
