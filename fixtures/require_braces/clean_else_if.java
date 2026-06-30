class ElseIfChain {
  String grade(int x) {
    if (x >= 90) {
      return "A";
    } else if (x >= 80) {
      return "B";
    } else {
      return "C";
    }
  }

  int sum(int[] xs) {
    int total = 0;
    for (int v : xs) {
      total += v;
    }
    return total;
  }
}
