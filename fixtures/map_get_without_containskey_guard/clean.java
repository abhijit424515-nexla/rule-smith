public class Clean {
  String upper(java.util.Map<String, String> m, String k) {
    if (m.containsKey(k)) {
      return m.get(k).toUpperCase();
    }
    return "";
  }
}
