public class Queue {
  synchronized void take() throws InterruptedException {
    wait();
    notifyAll();
  }
}
