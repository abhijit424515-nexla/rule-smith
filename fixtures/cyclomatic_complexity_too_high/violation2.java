public class MixedDecisions {
  boolean check(int a, int b, int c) {
    if (a > 0 && b > 0) return false;
    if (a < 0 || b < 0) return false;
    for (int i = 0; i < a; i++) {
      if (i == b && c > 0) return true;
    }
    while (c > 0 || a > 0) {
      c--;
      a--;
    }
    return a == b ? true : false;
  }
}
