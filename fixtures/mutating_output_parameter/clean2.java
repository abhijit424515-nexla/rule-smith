import java.util.List;

public class Reporter {
  public int countActive(List<User> users) {
    int n = 0;
    for (User u : users) {
      if (u.active()) {
        n++;
      }
    }
    return n;
  }
}
