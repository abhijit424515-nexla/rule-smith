class ElseForeachNoBrace {
  int score(int[] xs, boolean flag) {
    int total = 0;
    if (flag) {
      total = 1;
    } else total = 2;
    for (int x : xs) total += x;
    return total;
  }
}
