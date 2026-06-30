public class C {
  private final Service svc = new Service();

  public int compute(int a, int b) {
    return svc.compute(a + 1, b);
  }
}
