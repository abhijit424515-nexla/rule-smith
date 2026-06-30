import java.util.List;

public class CleanPure {
  public int computeTotal(List<Integer> items) {
    int s = 0;
    for (int i : items) {
      s += i;
    }
    return s;
  }
}
