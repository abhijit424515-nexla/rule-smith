import java.util.Optional;

public class ViolationNoElse {
  void print(Optional<String> name) {
    if (name.isPresent()) {
      System.out.println(name.get());
    }
  }
}
