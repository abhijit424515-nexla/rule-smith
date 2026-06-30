import java.util.List;
import java.util.stream.Collectors;

class V1 {
  void run(List<Integer> nums) {
    nums.stream().map(n -> n * 2).collect(Collectors.toList());
  }
}
