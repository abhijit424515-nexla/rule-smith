public class UserService {
  private int counter;
  private String lastUser;

  public void touch(String user) {
    this.counter++;
    this.lastUser = user;
  }
}
