public class V2 {
  void go() {
    Widget.Builder w = Widget.builder();
    w.id(1);
    Widget built = w.build();
    w.label("late");
    w.color("red");
  }
}
