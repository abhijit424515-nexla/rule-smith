import java.util.concurrent.ExecutorService;

class V2 {
  void run(ExecutorService exec, Runnable task) {
    exec.submit(task);
  }
}
