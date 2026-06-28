import java.io.InputStream;
class A {
  void f() {
    InputStream in = open();   // LEAK: never closed
    use(in);
  }
}
