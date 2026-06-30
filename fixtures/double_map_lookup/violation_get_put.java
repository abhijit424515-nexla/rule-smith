import java.util.ArrayList;
import java.util.List;
import java.util.Map;

class GetThenPut {
  void add(Map<String, List<String>> m, String k, String v) {
    if (m.get(k) == null) {
      m.put(k, new ArrayList<>());
    }
    m.get(k).add(v);
  }
}
