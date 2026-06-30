import java.io.IOException;
import java.io.InputStream;
import java.io.InvalidClassException;
import java.io.ObjectInputStream;
import java.io.ObjectStreamClass;

public class Safe2 {
  static final class Hardened extends ObjectInputStream {
    Hardened(InputStream in) throws IOException {
      super(in);
    }

    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc)
        throws IOException, ClassNotFoundException {
      if (!desc.getName().equals("com.acme.Allowed")) {
        throw new InvalidClassException("blocked");
      }
      return super.resolveClass(desc);
    }
  }

  Object load(InputStream in) throws Exception {
    return new Hardened(in).readObject();
  }
}
