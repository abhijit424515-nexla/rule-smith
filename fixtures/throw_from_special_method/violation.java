public class Widget {
  private final String name;

  public Widget(String name) {
    this.name = name;
  }

  @Override
  public String toString() {
    if (name == null) {
      throw new IllegalStateException("name not set");
    }
    return name;
  }
}
