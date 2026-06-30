public class Renderer {
  public String render(String text, boolean fancy) {
    if (fancy) {
      return "<b>" + text + "</b>";
    } else {
      return text;
    }
  }
}
