public final class Money {
  private final long amount;
  private final String currency;

  public Money(long amount, String currency) {
    this.amount = amount;
    this.currency = currency;
  }

  public long amount() {
    return amount;
  }
}
