import java.util.ArrayList;
import java.util.List;

public class CollectMutate {
  List<String> run(List<Integer> nums) {
    List<String> out = new ArrayList<>();
    nums.forEach(n -> out.add(String.valueOf(n)));
    return out;
  }
}
