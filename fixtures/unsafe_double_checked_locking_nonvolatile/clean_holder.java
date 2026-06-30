public class Resource {
  private Resource() {}

  private static class Holder {
    static final Resource INSTANCE = new Resource();
  }

  public static Resource getInstance() {
    return Holder.INSTANCE;
  }
}
