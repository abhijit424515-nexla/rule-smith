public class DeadStoreOverwrite {
  int f() {
    int x = 5;
    x = 10;
    return x;
  }
}
