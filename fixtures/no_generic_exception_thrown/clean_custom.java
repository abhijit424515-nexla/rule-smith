public class Loader {
  public void load(String path) {
    if (path == null) {
      throw new NotFoundException("missing path");
    }
  }
}
