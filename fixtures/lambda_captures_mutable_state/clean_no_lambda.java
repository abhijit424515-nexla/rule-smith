import java.util.ArrayList;
import java.util.List;

public class PlainLoop {
  List<String> run(List<Integer> nums) {
    List<String> out = new ArrayList<>();
    for (Integer n : nums) {
      out.add(String.valueOf(n));
    }
    return out;
  }
}
