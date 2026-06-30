import java.util.concurrent.CompletableFuture;

class V3 {
  void run() {
    CompletableFuture.supplyAsync(() -> compute()).thenApply(x -> x + 1);
  }

  int compute() {
    return 0;
  }
}
