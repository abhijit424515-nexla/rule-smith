import java.util.List;

public class Pick {
  String pick(List<String> items) {
    for (String s : items) {
      if (s.isEmpty()) {
        return "empty";
      } else {
        return s;
      }
    }
    return null;
  }
}
