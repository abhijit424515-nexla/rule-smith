public class CleanDefault {
  int len(java.util.Map<String, String> m, String k) {
    return m.getOrDefault(k, "").length();
  }
}
