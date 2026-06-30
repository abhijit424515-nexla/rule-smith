public class Money {
  final long cents;

  Money(long cents) {
    this.cents = cents;
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof Money && ((Money) o).cents == cents;
  }

  public boolean equals(Money other) {
    return other != null && other.cents == cents;
  }
}
