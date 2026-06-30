public class Order {
  String city(Customer c) {
    Address a = c.getAddress();
    City city = a.getCity();
    return city.getName().trim();
  }
}
