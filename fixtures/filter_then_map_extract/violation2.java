import java.util.List;
import java.util.stream.Collectors;

class V2 {
  List<Integer> run(List<String> xs) {
    return xs.stream()
        .filter(s -> s.length() > 3)
        .map(s -> s.length())
        .collect(Collectors.toList());
  }
}
