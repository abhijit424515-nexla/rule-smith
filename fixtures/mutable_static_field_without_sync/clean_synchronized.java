public class CleanSync {
  private static int count = 0;

  public void inc() {
    synchronized (CleanSync.class) {
      count++;
    }
  }
}
