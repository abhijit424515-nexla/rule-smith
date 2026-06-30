public class ArrayMutate {
  int total(int[] data) {
    int[] acc = new int[1];
    Runnable r = () -> acc[0] += data.length;
    r.run();
    return acc[0];
  }
}
