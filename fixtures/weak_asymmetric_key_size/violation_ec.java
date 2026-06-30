import java.security.KeyPairGenerator;

public class WeakEc {
  void gen() throws Exception {
    KeyPairGenerator g = KeyPairGenerator.getInstance("EC");
    g.initialize(192);
  }
}
