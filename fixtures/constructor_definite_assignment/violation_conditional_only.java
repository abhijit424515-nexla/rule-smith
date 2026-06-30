public class Account {
  private String owner;

  public Account(boolean named) {
    if (named) {
      this.owner = "system";
    }
  }
}
