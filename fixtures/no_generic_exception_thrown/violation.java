public class Order {
  public void validate(int qty) {
    if (qty < 0) {
      throw new RuntimeException("bad qty");
    }
  }
}
