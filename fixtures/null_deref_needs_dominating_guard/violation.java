public class Violation {
  int len(java.util.Map<String, String> m, String k) {
    String s = null;
    if (m.containsKey(k)) {
      s = m.get(k);
    }
    return s.length();
  }
}
