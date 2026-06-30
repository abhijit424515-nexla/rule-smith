import java.util.Map;

public class Lookup {
  String resolve(Map<String, String> m, String k) {
    try {
      if (!m.containsKey(k)) {
        throw new IllegalArgumentException("missing");
      }
      return m.get(k).trim();
    } catch (Exception e) {
      return "default";
    }
  }
}
