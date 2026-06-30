import javax.annotation.concurrent.GuardedBy;

class Counter {
  @GuardedBy("this")
  private int count;

  void inc() {
    count++;
  }
}
