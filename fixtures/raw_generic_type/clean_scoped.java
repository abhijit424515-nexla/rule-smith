import java.util.Map;

class CleanScoped {
  void inspect(Map<String, Integer> config) {
    for (Map.Entry<String, Integer> e : config.entrySet()) {
      e.getValue();
    }
  }
}
