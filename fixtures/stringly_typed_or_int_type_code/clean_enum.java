public class Order {
  enum Status {
    PREMIUM,
    STANDARD
  }

  private Status status;

  public double fee() {
    if (status == Status.PREMIUM) {
      return 0.0;
    }
    return 5.0;
  }
}
