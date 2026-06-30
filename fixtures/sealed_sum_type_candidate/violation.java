public class Payment {
  private String kind;
  private String cardNumber;
  private String bankAccount;
  private String walletId;

  public String describe() {
    switch (kind) {
      case "CARD":
        return cardNumber;
      case "BANK":
        return bankAccount;
      default:
        return walletId;
    }
  }
}
