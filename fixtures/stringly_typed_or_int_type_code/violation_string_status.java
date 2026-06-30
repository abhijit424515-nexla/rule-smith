public class Order {
  private String orderStatus;

  public double fee() {
    if (orderStatus.equals("PREMIUM")) {
      return 0.0;
    }
    return 5.0;
  }
}
