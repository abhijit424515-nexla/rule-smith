import java.io.BufferedReader;

class C {
  void m(BufferedReader r) throws Exception {
    String line;
    while ((line = r.readLine()) != null) {
      use(line);
    }
  }

  void use(String s) {}
}
