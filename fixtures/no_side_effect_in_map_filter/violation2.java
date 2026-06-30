import java.util.List;
import java.util.stream.Collectors;

public class IoInFilter {
  List<Integer> evens(List<Integer> nums) {
    return nums.stream()
        .filter(
            n -> {
              System.out.println("checking " + n);
              return n % 2 == 0;
            })
        .collect(Collectors.toList());
  }
}
