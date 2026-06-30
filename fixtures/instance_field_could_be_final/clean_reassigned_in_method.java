public class Counter {
  private int count;

  public Counter() {
    this.count = 0;
  }

  public void increment() {
    this.count = this.count + 1;
  }

  public int get() {
    return count;
  }
}
