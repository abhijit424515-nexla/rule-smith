public class Outer {
  @Override
  public int hashCode() {
    return 7;
  }

  static class Inner {
    private final String name;

    Inner(String name) {
      this.name = name;
    }

    @Override
    public boolean equals(Object o) {
      return o instanceof Inner && ((Inner) o).name.equals(name);
    }
  }
}
