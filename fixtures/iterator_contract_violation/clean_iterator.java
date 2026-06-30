import java.util.Iterator;
import java.util.NoSuchElementException;

public class CleanIterator implements Iterator<String> {
  private int i = 0;
  private final String[] a = {"a", "b"};

  public boolean hasNext() {
    return i < a.length;
  }

  public String next() {
    if (!hasNext()) {
      throw new NoSuchElementException();
    }
    return a[i++];
  }
}
