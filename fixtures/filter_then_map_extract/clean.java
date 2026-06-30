import java.util.List;
import java.util.stream.Collectors;

class C1 {
  List<String> run(List<String> xs) {
    return xs.stream()
        .filter(s -> s.length() > 3)
        .map(s -> s.toUpperCase())
        .collect(Collectors.toList());
  }
}
