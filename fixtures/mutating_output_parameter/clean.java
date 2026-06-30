import java.util.ArrayList;
import java.util.List;

public class Loader {
  public List<String> collectNames(List<User> users) {
    List<String> out = new ArrayList<>();
    for (User u : users) {
      out.add(u.name());
    }
    return out;
  }
}
