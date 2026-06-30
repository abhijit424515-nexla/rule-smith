import java.util.function.Supplier;

class C2 {
  Supplier<Integer> read() {
    try {
      return () -> 1;
    } finally {
      Runnable r =
          () -> {
            return;
          };
      r.run();
    }
  }
}
