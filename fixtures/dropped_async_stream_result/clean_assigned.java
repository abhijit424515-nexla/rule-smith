import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;

class C2 {
  void run(ExecutorService exec, Runnable task) {
    Future<?> f = exec.submit(task);
    f.cancel(false);
  }
}
