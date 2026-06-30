import java.util.List;

public class SideEffectInForEach {
  void log(List<Integer> ids, List<String> out) {
    ids.stream().filter(id -> id > 0).forEach(id -> out.add("id=" + id));
  }
}
