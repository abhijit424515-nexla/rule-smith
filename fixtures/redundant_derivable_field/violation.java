import java.util.ArrayList;
import java.util.List;

public class Cart {
  private List<String> items = new ArrayList<>();
  private int itemCount;

  public void add(String item) {
    items.add(item);
    itemCount++;
  }
}
