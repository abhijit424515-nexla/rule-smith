class Pick {
  int choose(boolean a, boolean b, int x, int y, int z) {
    return a ? (b ? x : y) : z;
  }
}
