import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;

public class V2 {
  public synchronized void await(Future<String> task)
      throws InterruptedException, ExecutionException {
    Future<String> fut = task;
    String r = fut.get();
    System.out.println(r);
  }
}
