import java.security.SecureRandom;

public class SecureToken {
  byte[] sessionToken() {
    SecureRandom sr = new SecureRandom();
    byte[] token = new byte[32];
    sr.nextBytes(token);
    return token;
  }
}
