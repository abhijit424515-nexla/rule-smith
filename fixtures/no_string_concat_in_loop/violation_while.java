public class B {
  String repeat(String unit, int n) {
    String out = "";
    int i = 0;
    while (i < n) {
      out += unit;
      i++;
    }
    return out;
  }
}
