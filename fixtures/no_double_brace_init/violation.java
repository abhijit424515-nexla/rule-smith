import java.util.HashMap;
import java.util.Map;

public class ViolationMap {
  public Map<String, Integer> build() {
    Map<String, Integer> m =
        new HashMap<String, Integer>() {
          {
            put("a", 1);
            put("b", 2);
          }
        };
    return m;
  }
}
