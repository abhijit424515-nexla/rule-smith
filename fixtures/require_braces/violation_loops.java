class LoopsNoBrace {
  int run(int[] xs) {
    int total = 0;
    for (int i = 0; i < xs.length; i++) total += xs[i];
    while (total > 100) total -= 10;
    return total;
  }
}
