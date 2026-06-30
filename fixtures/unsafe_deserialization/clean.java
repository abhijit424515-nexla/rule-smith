import java.io.InputStream;
import java.io.ObjectInputFilter;
import java.io.ObjectInputStream;

public class Safe1 {
  Object load(InputStream in) throws Exception {
    ObjectInputStream ois = new ObjectInputStream(in);
    ois.setObjectInputFilter(ObjectInputFilter.Config.createFilter("java.base/*;!*"));
    return ois.readObject();
  }
}
