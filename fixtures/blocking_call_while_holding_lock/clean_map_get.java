import java.util.HashMap;
import java.util.Map;

public class C2 {
  private final Map<String, String> cache = new HashMap<>();

  public synchronized String lookup(String k) {
    return cache.get(k);
  }
}
