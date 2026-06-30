public class D {
  int sum(int[] xs) {
    int total = 0;
    for (int x : xs) {
      total += x;
    }
    String label = "sum=";
    label += total;
    return total;
  }
}
