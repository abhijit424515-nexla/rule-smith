public class Violation {
  public void run(boolean fatal) {
    if (fatal) {
      System.exit(1);
    }
  }
}
