import java.security.KeyPairGenerator;

public class WeakRsa {
  void gen() throws Exception {
    KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
    kpg.initialize(1024);
  }
}
