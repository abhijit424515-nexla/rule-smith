public class ViolationNested {
  int run(boolean x) {
    try {
      work();
    } finally {
      if (x) {
        return 0;
      }
    }
    return -1;
  }

  void work() {}
}
