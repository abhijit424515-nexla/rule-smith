public class V1 {
  private final Object lock = new Object();

  public void run() throws InterruptedException {
    synchronized (lock) {
      doWork();
      Thread.sleep(1000);
    }
  }

  private void doWork() {}
}
