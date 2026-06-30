public class Calc {
  int total(java.util.List<Integer> xs) {
    int sum = 0;
    for (int x : xs) {
      sum += x;
    }
    return sum;
  }
}
