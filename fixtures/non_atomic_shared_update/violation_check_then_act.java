import javax.annotation.concurrent.GuardedBy;

class Stats {
  @GuardedBy("this")
  private long total;

  void bump() {
    total = total + 1;
  }
}
