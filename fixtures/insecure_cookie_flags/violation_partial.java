import javax.servlet.http.Cookie;

public class PartialFlags {
  void issue() {
    Cookie token = new Cookie("AUTH", "xyz");
    token.setSecure(true);
  }
}
