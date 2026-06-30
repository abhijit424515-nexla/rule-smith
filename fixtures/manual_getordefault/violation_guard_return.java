import java.util.Map;

class ViolationGuardReturn {
  String lookup(Map<String, String> m, String k) {
    if (m.containsKey(k)) {
      return m.get(k);
    }
    return "default";
  }
}
