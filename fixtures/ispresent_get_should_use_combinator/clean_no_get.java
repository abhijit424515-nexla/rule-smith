import java.util.Optional;

public class CleanNoGet {
  boolean has(Optional<String> name) {
    if (name.isPresent()) {
      return true;
    }
    return false;
  }
}
