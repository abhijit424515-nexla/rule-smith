import java.util.List;

public class CartValidator {
  void validate(List<String> items, String sku) {
    assert items.add(sku);
    process(items);
  }

  void process(List<String> items) {}
}
