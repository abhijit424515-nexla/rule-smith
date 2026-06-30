import java.util.List;
import java.util.Optional;

public class LocalUse {
  public Optional<String> first(List<String> xs) {
    Optional<String> r = xs.stream().findFirst();
    return r;
  }
}
