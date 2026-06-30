public class FieldWrite {
  private int total;

  @Pure
  public int addUp(int n) {
    this.total = n * 2;
    return this.total;
  }
}
