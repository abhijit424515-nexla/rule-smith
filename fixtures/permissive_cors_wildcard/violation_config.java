import org.springframework.web.cors.CorsConfiguration;

public class CorsConfig {
  public CorsConfiguration build() {
    CorsConfiguration cfg = new CorsConfiguration();
    cfg.addAllowedOrigin("*");
    cfg.setAllowCredentials(true);
    return cfg;
  }
}
