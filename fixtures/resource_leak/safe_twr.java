import java.io.InputStream;
class A {
  void f() {
    try (InputStream in = open()) { use(in); }  // SAFE: try-with-resources
  }
}
