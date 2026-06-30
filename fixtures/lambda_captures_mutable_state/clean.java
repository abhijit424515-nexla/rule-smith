import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class LocalOnly {
  List<String> run(List<Integer> nums) {
    return nums.stream()
        .map(
            n -> {
              List<String> local = new ArrayList<>();
              local.add(String.valueOf(n));
              return local.get(0);
            })
        .collect(Collectors.toList());
  }
}
