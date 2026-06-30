import java.util.List;
import org.springframework.web.cors.CorsConfiguration;

public class CorsConfigStrict {
  public CorsConfiguration build() {
    CorsConfiguration cfg = new CorsConfiguration();
    cfg.setAllowedOrigins(List.of("https://a.example.com", "https://b.example.com"));
    return cfg;
  }
}
