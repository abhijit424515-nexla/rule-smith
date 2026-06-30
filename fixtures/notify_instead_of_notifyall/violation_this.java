public class Latch {
  private boolean done;

  public synchronized void release() {
    done = true;
    this.notify();
  }

  public synchronized void await() throws InterruptedException {
    while (!done) {
      wait();
    }
  }
}
