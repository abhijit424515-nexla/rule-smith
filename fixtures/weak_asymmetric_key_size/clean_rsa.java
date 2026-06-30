import java.security.KeyPairGenerator;

public class StrongRsa {
  void gen() throws Exception {
    KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
    kpg.initialize(2048);
  }
}
