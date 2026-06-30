import java.util.Optional;

class GoodLookup {
  Optional<String> lookup(int id) {
    if (id < 0) {
      return Optional.empty();
    }
    return Optional.of("x");
  }
}
