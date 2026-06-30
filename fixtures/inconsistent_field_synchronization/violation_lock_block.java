class Bank {
  private final Object lock = new Object();
  private int balance;

  void deposit(int n) {
    synchronized (lock) {
      balance += n;
    }
  }

  int peek() {
    return balance;
  }
}
