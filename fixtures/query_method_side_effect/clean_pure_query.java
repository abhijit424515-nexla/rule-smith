public class D {
  private int total;

  public void addOne() {
    total++;
  }

  public boolean shouldRetry(int n) {
    return n < 3;
  }

  public String getLabel(int n) {
    return n > 0 ? "pos" : "neg";
  }
}
