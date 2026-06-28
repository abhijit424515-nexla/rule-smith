import java.io.InputStream;
class A {
  void f() {
    InputStream in = open();
    try { use(in); } finally { in.close(); }   // SAFE
  }
}
