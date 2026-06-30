import java.util.Optional;

class RealMap {
  Optional<String> g(Optional<String> o) {
    return o.map(s -> s.trim());
  }
}
