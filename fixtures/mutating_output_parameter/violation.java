import java.util.List;

public class Loader {
  public void collectNames(List<User> users, List<String> out) {
    for (User u : users) {
      out.add(u.name());
    }
  }
}
