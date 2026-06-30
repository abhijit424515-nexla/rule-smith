import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

class C2 {
  List<String> run(List<Optional<String>> xs) {
    return xs.stream().flatMap(Optional::stream).collect(Collectors.toList());
  }
}
