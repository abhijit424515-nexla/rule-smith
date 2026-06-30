import java.util.Optional;

class Cache {
  private Optional<Object> value = Optional.empty();

  boolean present() {
    return value.isPresent();
  }
}
