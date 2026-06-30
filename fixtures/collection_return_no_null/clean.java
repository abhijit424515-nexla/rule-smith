import java.util.Collections;
import java.util.List;

class Repo {
  List<String> names(boolean empty) {
    if (empty) {
      return Collections.emptyList();
    }
    return Collections.singletonList("a");
  }
}
