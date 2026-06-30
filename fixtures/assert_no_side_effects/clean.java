import java.util.List;

public class CartValidator {
  void validate(List<String> items, String sku) {
    assert items.contains(sku) && items.size() > 0;
    process(items);
  }

  void process(List<String> items) {}
}
