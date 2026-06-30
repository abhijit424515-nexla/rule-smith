public class Order {
  private final String id;
  private final String customer;
  private final String address;
  private final int quantity;
  private final double price;
  private final boolean express;

  public Order(
      String id, String customer, String address, int quantity, double price, boolean express) {
    this.id = id;
    this.customer = customer;
    this.address = address;
    this.quantity = quantity;
    this.price = price;
    this.express = express;
  }
}
