import java.util.List;
import java.util.stream.Collectors;

class C1 {
  List<Integer> run(List<Integer> nums) {
    return nums.stream().map(n -> n * 2).collect(Collectors.toList());
  }
}
