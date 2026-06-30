import java.util.concurrent.ConcurrentHashMap;

public class CleanConcurrent {
  private static ConcurrentHashMap<String, String> map = new ConcurrentHashMap<>();

  public void put(String k, String v) {
    map.put(k, v);
  }
}
