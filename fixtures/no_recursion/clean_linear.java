public class Pipeline {
  int run(int x) {
    return stepTwo(stepOne(x));
  }

  int stepOne(int x) {
    return x + 1;
  }

  int stepTwo(int x) {
    return x * 2;
  }
}
