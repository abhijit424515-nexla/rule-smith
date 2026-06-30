import java.util.Map;

class ContainsThenGet {
  int score(Map<String, Integer> m) {
    if (m.containsKey("x")) {
      return m.get("x");
    }
    return 0;
  }
}
