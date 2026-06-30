import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

class V1 {
  List<String> run(List<Optional<String>> xs) {
    return xs.stream().filter(o -> o.isPresent()).map(o -> o.get()).collect(Collectors.toList());
  }
}
