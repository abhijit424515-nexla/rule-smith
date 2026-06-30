import java.util.List;
import java.util.stream.Collectors;

class RealTransform {
  List<Integer> f(List<String> xs) {
    return xs.stream().map(x -> x.length()).collect(Collectors.toList());
  }
}
