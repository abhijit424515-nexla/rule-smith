public class B {
  private String name;

  public String getName() {
    name = name.trim();
    return name;
  }

  public boolean isReady() {
    reset();
    save();
    return true;
  }

  void reset() {}

  void save() {}
}
