import java.util.Optional;

public class UserService {
  String name(Optional<String> maybe) {
    Optional<String> o = maybe;
    return o.get();
  }
}
