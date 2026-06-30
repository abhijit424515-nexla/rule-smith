public class UserSettings {
  private String theme;
  private int fontSize;

  public UserSettings(String theme, int fontSize) {
    this.theme = theme;
    this.fontSize = fontSize;
  }

  public void setTheme(String theme) {
    this.theme = theme;
  }
}
