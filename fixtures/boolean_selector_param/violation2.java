public class Calc {
  public int compute(int x, boolean useCache) {
    int base = x * 2;
    return useCache ? base + cached() : base + fresh();
  }

  private int cached() {
    return 1;
  }

  private int fresh() {
    return 2;
  }
}
