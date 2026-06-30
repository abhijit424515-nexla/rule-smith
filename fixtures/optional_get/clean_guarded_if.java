import java.util.Optional;

class A {
  String f() {
    Optional<String> o = find();
    if (o.isPresent()) {
      return o.get();
    }
    return "";
  }
}
