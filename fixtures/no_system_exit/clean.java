public class Clean {
  public int run(boolean fatal) {
    if (fatal) {
      throw new IllegalStateException("fatal");
    }
    System.out.println("ok");
    return 0;
  }
}
