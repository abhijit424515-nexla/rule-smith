public class Config {
  private Config cached;

  public Config get() {
    if (this.cached == null) {
      synchronized (this) {
        if (this.cached == null) {
          this.cached = load();
        }
      }
    }
    return this.cached;
  }

  private Config load() {
    return new Config();
  }
}
