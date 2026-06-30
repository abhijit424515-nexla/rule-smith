import java.security.SecureRandom;
import javax.crypto.spec.IvParameterSpec;

public class C {
  IvParameterSpec make() {
    byte[] iv = new byte[16];
    new SecureRandom().nextBytes(iv);
    return new IvParameterSpec(iv);
  }
}
