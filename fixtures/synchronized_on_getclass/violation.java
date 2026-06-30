public class Cache {
  public void clear() {
    synchronized (getClass()) {
      System.out.println("cleared");
    }
  }
}
