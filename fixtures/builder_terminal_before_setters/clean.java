public class C1 {
  Foo make() {
    Foo.Builder b = Foo.builder();
    b.name("x");
    b.age(3);
    return b.build();
  }
}
