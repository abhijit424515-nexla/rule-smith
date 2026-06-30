import java.util.ArrayList;
import java.util.List;

class Repo {
  List<String> names(boolean empty) {
    if (empty) {
      return null;
    }
    return new ArrayList<>();
  }
}
