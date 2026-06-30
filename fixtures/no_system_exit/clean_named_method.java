public class CleanNamedMethod {
  public void run() {
    exit(0);
  }

  private void exit(int code) {
    // local helper, not System.exit
  }
}
