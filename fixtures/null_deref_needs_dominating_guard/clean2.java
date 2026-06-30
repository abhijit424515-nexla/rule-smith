public class Clean2 {
  int len(java.util.Map<String, String> m, String k) {
    String s = null;
    if (m.containsKey(k)) {
      s = m.get(k);
    }
    if (s == null) {
      return 0;
    }
    return s.length();
  }
}
