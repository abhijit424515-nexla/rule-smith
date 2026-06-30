public class B {
  void run() {
    try {
      Thread.sleep(100);
    } catch (InterruptedException e) {
      System.out.println("interrupted: " + e.getMessage());
    }
  }
}
