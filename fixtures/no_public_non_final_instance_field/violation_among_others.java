public class Config {
  private final String id = "x";
  public String name;
  protected int count;

  public String describe() {
    return id + name + count;
  }
}
