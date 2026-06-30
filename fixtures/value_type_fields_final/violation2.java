@Value
public class Money {
  private long cents;
  private final String currency;

  public Money(long cents, String currency) {
    this.cents = cents;
    this.currency = currency;
  }
}
