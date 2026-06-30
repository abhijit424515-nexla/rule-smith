public class Find {
  int find(int[] xs, int target) {
    for (int i = 0; i < xs.length; i++) {
      if (xs[i] == target) {
        return i;
      }
    }
    return -1;
  }
}
