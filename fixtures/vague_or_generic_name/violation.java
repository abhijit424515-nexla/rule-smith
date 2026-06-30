public class Loader {
  void process() {
    int data = compute();
    int next = data + 1;
    System.out.println(next);
  }

  int compute() {
    return 42;
  }
}
