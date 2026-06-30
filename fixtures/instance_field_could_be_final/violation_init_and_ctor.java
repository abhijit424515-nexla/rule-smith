public class Config {
  private String name = "default";
  private int count;

  public Config(int count) {
    this.count = count;
  }

  public String name() {
    return name;
  }

  public int count() {
    return count;
  }
}
