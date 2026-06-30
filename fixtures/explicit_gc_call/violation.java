public class Cleaner {
  void cleanup() {
    doWork();
    System.gc();
  }

  void doWork() {}
}
