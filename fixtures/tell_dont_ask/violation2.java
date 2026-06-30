class OrderService {
  void apply(Cart cart) {
    if (cart.isEmpty()) {
      cart.setStatus("EMPTY");
    } else {
      cart.setStatus("READY");
    }
  }
}
