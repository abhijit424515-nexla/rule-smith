import javax.crypto.spec.IvParameterSpec;

public class Viv {
  IvParameterSpec make() {
    byte[] iv = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    return new IvParameterSpec(iv);
  }
}
