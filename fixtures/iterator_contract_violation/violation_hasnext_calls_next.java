import java.util.Iterator;
import java.util.NoSuchElementException;

public class HasNextCallsNext implements Iterator<String> {
  private int i = 0;
  private final String[] a = {"x", "y"};

  public boolean hasNext() {
    return next() != null;
  }

  public String next() {
    if (i >= a.length) {
      throw new NoSuchElementException();
    }
    return a[i++];
  }
}
