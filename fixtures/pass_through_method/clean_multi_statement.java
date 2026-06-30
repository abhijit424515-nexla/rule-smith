public class D {
  private final Repo repo = new Repo();

  public void save(String name, String value) {
    log(name);
    repo.save(name, value);
  }

  void log(String s) {}
}
