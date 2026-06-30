import java.util.Map;

class DifferentKeys {
  int sum(Map<String, Integer> m) {
    return m.get("a") + m.get("b");
  }
}
