import java.util.Map;

class CleanContainsKeyOnly {
  boolean has(Map<String, Integer> m, String k) {
    if (m.containsKey(k)) {
      return true;
    }
    return false;
  }
}
