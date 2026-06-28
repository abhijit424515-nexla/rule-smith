import java.io.InputStream;
class A {
  void f(boolean err) {
    InputStream in = open();   // LEAK: close skipped on early return
    if (err) { return; }
    in.close();
  }
}
