import java.beans.XMLDecoder;
import java.io.InputStream;

public class Vuln2 {
  Object load(InputStream in) {
    return new XMLDecoder(in).readObject();
  }
}
