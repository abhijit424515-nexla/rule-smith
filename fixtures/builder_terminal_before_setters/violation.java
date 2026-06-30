public class V1 {
  Foo make() {
    Foo.Builder b = Foo.builder();
    b.name("x");
    Foo f = b.build();
    b.age(3);
    return f;
  }
}
