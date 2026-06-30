class AllBraced {
  int classify(int x) {
    if (x > 0) {
      return 1;
    }
    for (int i = 0; i < x; i++) {
      x--;
    }
    while (x > 0) {
      x--;
    }
    return 0;
  }
}
