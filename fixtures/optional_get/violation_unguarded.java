import java.util.Optional;

class A {
  String f() {
    Optional<String> o = find();
    return o.get();
  }
}
