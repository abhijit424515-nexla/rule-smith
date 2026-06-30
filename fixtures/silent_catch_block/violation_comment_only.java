public class B {
  int g(String s) {
    int x = 0;
    try {
      x = Integer.parseInt(s);
    } catch (NumberFormatException e) {
      // ignore, parsing can fail
    }
    return x;
  }
}
