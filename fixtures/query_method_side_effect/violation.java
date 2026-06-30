public class A {
  private int count;
  private java.util.List<String> items = new java.util.ArrayList<>();

  public int getCount() {
    this.count++;
    return count;
  }

  public boolean hasItems() {
    items.add("x");
    return !items.isEmpty();
  }
}
