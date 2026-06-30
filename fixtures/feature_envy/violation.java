class PriceFormatter {
  String describe(Order order) {
    return order.getName()
        + " "
        + order.getTotal()
        + " "
        + order.getTax()
        + " "
        + order.getDiscount();
  }
}
