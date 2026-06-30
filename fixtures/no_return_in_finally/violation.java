public class Violation {
  int compute() {
    try {
      return 1;
    } finally {
      return 9;
    }
  }
}
