public class Account {
  private final long id;

  public Account(long id) {
    this.id = id;
  }

  @Override
  public String toString() {
    return "Account#" + id;
  }

  @Override
  public int hashCode() {
    try {
      return Long.hashCode(id);
    } catch (RuntimeException e) {
      return 0;
    }
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof Account && ((Account) o).id == id;
  }
}
