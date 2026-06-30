import java.io.InputStream;

class A {
  InputStream f() {
    InputStream in = open(); // SAFE: ownership returned to caller
    return in;
  }
}
