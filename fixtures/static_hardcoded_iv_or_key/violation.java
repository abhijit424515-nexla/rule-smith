import javax.crypto.spec.SecretKeySpec;

public class V {
  SecretKeySpec make() {
    return new SecretKeySpec("1234567890123456".getBytes(), "AES");
  }
}
