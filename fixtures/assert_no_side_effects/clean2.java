import com.google.common.base.Preconditions;

public class Counter {
  int index = 0;

  int next(int limit) {
    Preconditions.checkArgument(index < limit, "overflow");
    index = index + 1;
    return index;
  }
}
