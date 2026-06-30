import java.util.List;
import java.util.stream.Collectors;

class StreamIdentity {
  List<String> f(List<String> xs) {
    return xs.stream().map(x -> x).collect(Collectors.toList());
  }
}
