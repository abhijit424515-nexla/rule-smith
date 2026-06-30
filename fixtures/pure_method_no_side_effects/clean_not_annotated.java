public class NotPure {
  private int total;

  public void add(int n) {
    this.total += n;
    System.out.println(total);
  }
}
