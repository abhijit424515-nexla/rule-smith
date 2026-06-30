public class Ok {
  private String token = System.getenv("TOKEN");

  void f() {
    String username = "alice";
    int retries = 3;
    System.out.println(username + retries);
  }
}
