public class Money {
  private final long cents;

  public Money(long cents) {
    this.cents = cents;
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof Money && ((Money) o).cents == cents;
  }

  @Override
  public int hashCode() {
    return Long.hashCode(cents);
  }
}
