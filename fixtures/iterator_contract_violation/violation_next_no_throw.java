import java.util.Iterator;

public class NextNoThrow implements Iterator<Integer> {
  private int i = 0;
  private final int[] a = {1, 2, 3};

  public boolean hasNext() {
    return i < a.length;
  }

  public Integer next() {
    return a[i++];
  }
}
