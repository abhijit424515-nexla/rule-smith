import java.util.HashMap;
import java.util.Map;

public class Cache {
  private static Map<String, String> cache = new HashMap<>();

  public void put(String k, String v) {
    cache.put(k, v);
  }
}
