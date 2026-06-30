import java.util.Optional;

class Lookup {
  Optional<String> lookup(int id) {
    if (id < 0) {
      return null;
    }
    return Optional.of("x");
  }
}
