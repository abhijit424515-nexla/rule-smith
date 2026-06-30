public class Flagged {
  private boolean enabled;

  public void configure(boolean enabled) {
    this.enabled = enabled;
  }

  public boolean isEnabled() {
    return enabled;
  }
}
