import java.util.Optional;

public class CleanCombinator {
  String label(Optional<String> name) {
    return name.map(n -> n).orElse("unknown");
  }
}
