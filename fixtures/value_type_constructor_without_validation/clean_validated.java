public final class Money {
  private final long amount;
  private final String currency;

  public Money(long amount, String currency) {
    if (amount < 0) {
      throw new IllegalArgumentException("amount must be non-negative");
    }
    this.amount = amount;
    this.currency = currency;
  }
}
