import java.util.ArrayList;
import java.util.List;

public class Cart {
  private List<String> items = new ArrayList<>();
  private String owner;

  public int size() {
    return items.size();
  }
}
