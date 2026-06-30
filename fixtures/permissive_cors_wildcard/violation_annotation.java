import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class OpenController {
  @CrossOrigin(origins = "*", allowCredentials = "true")
  public String all() {
    return "data";
  }
}
