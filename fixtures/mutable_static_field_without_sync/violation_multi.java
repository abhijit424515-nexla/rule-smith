public class Counter {
  private static int count = 0;
  private static int[] buckets = new int[10];

  public void inc(int i) {
    count++;
    buckets[i]++;
  }
}
