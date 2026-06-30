class Violation2 {
  boolean cmp(@Unsigned long a, @Signed long b) {
    return a < b;
  }

  int shift(@Unsigned int x) {
    return x >> 2;
  }
}
