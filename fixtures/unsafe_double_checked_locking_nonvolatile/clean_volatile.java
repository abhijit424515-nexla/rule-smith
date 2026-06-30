public class Lazy {
  private static volatile Lazy instance;

  public static Lazy getInstance() {
    if (instance == null) {
      synchronized (Lazy.class) {
        if (instance == null) {
          instance = new Lazy();
        }
      }
    }
    return instance;
  }
}
