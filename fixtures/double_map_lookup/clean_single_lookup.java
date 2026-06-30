import java.util.Map;

class SingleLookup {
  int score(Map<String, Integer> m) {
    return m.getOrDefault("x", 0);
  }
}
