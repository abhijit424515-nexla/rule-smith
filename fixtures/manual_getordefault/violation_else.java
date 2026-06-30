import java.util.Map;

class ViolationElse {
  int lookup(Map<String, Integer> m, String k) {
    if (m.containsKey(k)) {
      return m.get(k);
    } else {
      return 0;
    }
  }
}
