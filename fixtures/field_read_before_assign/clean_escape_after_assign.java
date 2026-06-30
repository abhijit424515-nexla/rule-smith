public class Widget {
  private final int id;

  public Widget(Registry r) {
    this.id = 7;
    r.register(this);
  }
}
