public class IoCall {
  @SideEffectFree
  public int log(int n) {
    System.out.println(n);
    return n;
  }
}
