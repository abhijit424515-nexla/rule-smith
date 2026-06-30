public class Config {
  private static final int MAX_RETRIES = 5;
  public static final String DEFAULT_NAME = "x";

  public int get() {
    return MAX_RETRIES;
  }
}
