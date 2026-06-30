public class Renamer {
  private String name;

  void rebind() {
    String name = compute();
    use(name);
  }

  String compute() {
    return "x";
  }

  void use(String s) {}
}
