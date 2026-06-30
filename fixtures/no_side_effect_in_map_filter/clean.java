import java.util.List;
import java.util.stream.Collectors;

public class PureMap {
  List<String> names(List<Integer> ids) {
    return ids.stream().map(id -> "id=" + id).collect(Collectors.toList());
  }
}
