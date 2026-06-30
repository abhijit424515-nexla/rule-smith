import java.util.List;
import javax.annotation.concurrent.Immutable;

@Immutable
public final class Roster {
  private final List<String> members;

  Roster(List<String> members) {
    this.members = members;
  }
}
