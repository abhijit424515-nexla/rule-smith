public class ConfigReaderOk {
  public String read(Config config) {
    if (config == null || config.getValue() != null) {
      return "x";
    }
    return "";
  }
}
