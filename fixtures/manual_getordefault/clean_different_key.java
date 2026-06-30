import java.util.Map;

class CleanDifferentKey {
  int lookup(Map<String, Integer> m, String k1, String k2) {
    if (m.containsKey(k1)) {
      return m.get(k2);
    }
    return 0;
  }
}
