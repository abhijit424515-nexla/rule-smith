public class ConfigDto {
  private static int instances;
  private final int port;

  public ConfigDto(int port) {
    this.port = port;
    instances++;
  }
}
