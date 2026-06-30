class AfterReturn {
  int compute(int x) {
    return x * 2;
    System.out.println("never runs");
  }
}
