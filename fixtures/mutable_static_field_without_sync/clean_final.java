import java.util.HashMap;
import java.util.Map;

public class CleanFinal {
  private static final Map<String, String> CACHE = new HashMap<>();

  public synchronized void put(String k, String v) {
    CACHE.put(k, v);
  }
}
