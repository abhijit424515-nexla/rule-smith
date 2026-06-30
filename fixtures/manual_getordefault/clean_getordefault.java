import java.util.Map;

class CleanGetOrDefault {
  int lookup(Map<String, Integer> m, String k) {
    return m.getOrDefault(k, 0);
  }
}
