class AccountService {
  void normalize(Wallet w) {
    if (w.getBalance() < 0) {
      w.setBalance(0);
    }
  }
}
