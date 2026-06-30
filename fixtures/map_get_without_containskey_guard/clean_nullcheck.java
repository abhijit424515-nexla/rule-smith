public class CleanNullCheck {
  int len(java.util.Map<String, String> m, String k) {
    String v = m.get(k);
    if (v != null) {
      return v.length();
    }
    return 0;
  }
}
