public class Registry {
  private static String name = "x";
  public static long total = 0L;

  public void reset() {
    name = "y";
    total = 0L;
  }
}
