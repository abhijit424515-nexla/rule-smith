import java.util.List;
import java.util.Map;

public class Lookup {
  String find(Map<String, String> m, List<String> xs) {
    String a = m.get("k");
    String b = xs.get(0);
    return a + b;
  }
}
