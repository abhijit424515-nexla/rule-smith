public class Order {
  public void validate(int qty) {
    if (qty < 0) {
      throw new IllegalArgumentException("qty must be >= 0");
    }
  }
}
