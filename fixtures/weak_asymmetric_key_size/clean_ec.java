import java.security.KeyPairGenerator;

public class StrongEc {
  void gen() throws Exception {
    KeyPairGenerator g = KeyPairGenerator.getInstance("EC");
    g.initialize(256);
  }
}
