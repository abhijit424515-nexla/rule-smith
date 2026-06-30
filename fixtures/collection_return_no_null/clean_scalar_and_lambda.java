import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

class Mixed {
  String first() {
    return null;
  }

  Map<String, String> build() {
    Supplier<Object> s =
        () -> {
          return null;
        };
    return new HashMap<>();
  }
}
