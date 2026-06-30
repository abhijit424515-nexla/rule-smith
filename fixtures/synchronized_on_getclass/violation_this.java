public class Registry {
  private int n;

  public void inc() {
    synchronized (this.getClass()) {
      n++;
    }
  }
}
