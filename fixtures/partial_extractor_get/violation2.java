import io.vavr.control.Either;
import io.vavr.control.Try;

public class Loader {
  int load(Try<Integer> t, Either<String, Integer> e) {
    int v = t.get();
    int r = e.right().get();
    return v + r;
  }
}
