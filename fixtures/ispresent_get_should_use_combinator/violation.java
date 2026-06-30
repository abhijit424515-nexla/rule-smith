import java.util.Optional;

public class Violation {
  String label(Optional<String> name) {
    if (name.isPresent()) {
      return name.get();
    } else {
      return "unknown";
    }
  }
}
