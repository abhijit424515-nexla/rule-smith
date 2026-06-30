import java.util.List;
import java.util.stream.Collectors;

public class CollectInMap {
  List<String> names(List<Integer> ids, List<String> log) {
    return ids.stream()
        .map(
            id -> {
              log.add("seen " + id);
              return "id=" + id;
            })
        .collect(Collectors.toList());
  }
}
