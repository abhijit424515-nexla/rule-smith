class SignedOnly {
  int k(@Signed int a, int b) {
    return a / b + (a < b ? 1 : 0);
  }
}
