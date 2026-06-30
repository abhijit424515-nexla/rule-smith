import org.springframework.web.bind.annotation.CrossOrigin;

public class ScopedController {
  @CrossOrigin(origins = "https://trusted.example.com")
  public String ok() {
    return "data";
  }
}
