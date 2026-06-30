import java.io.InputStream;
import java.io.ObjectInputStream;

public class Vuln1 {
  Object load(InputStream in) throws Exception {
    ObjectInputStream ois = new ObjectInputStream(in);
    return ois.readObject();
  }
}
