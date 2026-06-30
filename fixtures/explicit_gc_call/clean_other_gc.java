public class Custom {
  private final Janitor janitor = new Janitor();

  void tidy() {
    janitor.gc();
  }

  static class Janitor {
    void gc() {}
  }
}
