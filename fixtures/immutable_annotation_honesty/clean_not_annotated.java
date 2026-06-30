import java.util.List;

public final class MutableBag {
  private int size;
  private final List<String> items;

  MutableBag(List<String> items) {
    this.items = items;
  }

  List<String> items() {
    return items;
  }
}
