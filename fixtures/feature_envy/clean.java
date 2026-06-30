class Account {
  private long balance;
  private long limit;

  boolean canWithdraw(Bank bank) {
    return this.balance > 0 && this.limit > 0 && available() && bank.isOpen();
  }

  boolean available() {
    return this.balance < this.limit;
  }
}
