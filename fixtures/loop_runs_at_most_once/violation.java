public class FirstElement {
  int first(int[] xs) {
    for (int x : xs) {
      return x;
    }
    return -1;
  }
}
