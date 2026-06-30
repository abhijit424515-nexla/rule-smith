public class A {
  void run() {
    try {
      Thread.sleep(100);
    } catch (InterruptedException e) {
      // swallowed: signal lost
    }
  }
}
