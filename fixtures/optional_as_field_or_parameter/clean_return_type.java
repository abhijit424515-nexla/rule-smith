import java.util.Optional;

public class ReturnsOptional {
  private String name;

  public Optional<String> findName() {
    return Optional.ofNullable(name);
  }
}
