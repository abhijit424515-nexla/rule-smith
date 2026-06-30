import javax.annotation.concurrent.GuardedBy;

class Counter {
  @GuardedBy("this")
  private int count;

  synchronized void inc() {
    count++;
  }
}
