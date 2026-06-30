public class Widget {
  private final int id;

  public Widget(Registry r) {
    r.register(this);
    this.id = 7;
  }
}
