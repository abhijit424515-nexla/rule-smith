public class Clean {
  void run() {
    try {
      doWork();
    } finally {
      cleanup();
    }
  }

  void doWork() {}

  void cleanup() {}
}
