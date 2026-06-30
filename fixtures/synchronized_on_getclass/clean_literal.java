public class Cache {
  public void clear() {
    synchronized (Cache.class) {
      System.out.println("cleared");
    }
  }
}
