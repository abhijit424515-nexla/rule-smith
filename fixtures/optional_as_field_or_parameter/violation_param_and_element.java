import java.util.List;
import java.util.Optional;

public class ParamAndElement {
  public void process(List<Optional<String>> items, Optional<Integer> count) {
    // Optional<String> as collection element -> 1
    // Optional<Integer> as parameter        -> 1
  }
}
