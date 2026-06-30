import java.util.ArrayList;
import java.util.List;

public class ViolationList {
  public List<String> names() {
    return new ArrayList<String>() {
      {
        add("x");
        add("y");
      }
    };
  }
}
