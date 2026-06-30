public class ConfigReader {
  public String read(Config config) {
    if (config == null && config.getValue() != null) {
      return config.getValue();
    }
    return "";
  }
}
