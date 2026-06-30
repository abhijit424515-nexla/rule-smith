class C2 {
  long sum(Number n, int d) {
    long total = (long) d;
    if (n instanceof Long) {
      Long boxed = (Long) n;
      total += boxed;
    }
    return total;
  }
}
