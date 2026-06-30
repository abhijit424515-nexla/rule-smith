public class ViolationTwo {
  public void main(String[] args) {
    if (args.length == 0) {
      System.exit(2);
    }
    doWork();
    System.exit(0);
  }

  void doWork() {}
}
