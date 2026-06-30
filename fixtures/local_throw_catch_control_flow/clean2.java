import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class Reader2 {
  String read(String path) {
    try (BufferedReader r = new BufferedReader(new FileReader(path))) {
      return r.readLine();
    } catch (IOException e) {
      return null;
    }
  }
}
