import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;

public class Roster implements Serializable {
  private String[] names;
  private java.util.List<String> tags;

  public Roster(String[] names) {
    this.names = names;
  }

  private void readObject(ObjectInputStream s) throws IOException, ClassNotFoundException {
    s.defaultReadObject();
  }
}
