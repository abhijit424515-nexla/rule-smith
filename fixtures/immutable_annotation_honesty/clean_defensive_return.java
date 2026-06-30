import javax.annotation.concurrent.Immutable;

@Immutable
public final class Settings {
  private final boolean enabled;
  private final long createdAt;

  Settings(boolean enabled, long createdAt) {
    this.enabled = enabled;
    this.createdAt = createdAt;
  }

  boolean enabled() {
    return enabled;
  }
}
