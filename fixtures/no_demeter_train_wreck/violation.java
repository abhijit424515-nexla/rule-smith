public class Order {
  String city(Customer c) {
    return c.getAddress().getCity().getName().trim();
  }
}
