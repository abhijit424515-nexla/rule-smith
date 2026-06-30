public class Resource {
  private java.io.InputStream stream;

  @Override
  protected void finalize() throws Throwable {
    if (stream != null) {
      stream.close();
    }
    super.finalize();
  }
}
