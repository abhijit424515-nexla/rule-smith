import java.util.Optional;

class OptionalIdentity {
  Optional<String> g(Optional<String> o) {
    return o.map(
        s -> {
          return s;
        });
  }
}
