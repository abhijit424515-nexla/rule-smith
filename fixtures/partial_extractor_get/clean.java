import java.util.Optional;

public class UserService {
  String name(Optional<String> o) {
    return o.orElse("anon");
  }
}
