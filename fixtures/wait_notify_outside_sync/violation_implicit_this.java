public class Queue {
  synchronized void other() {}

  void take() throws InterruptedException {
    this.wait();
  }
}
