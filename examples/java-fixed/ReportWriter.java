package examples;

import java.io.FileOutputStream;
import java.io.IOException;

public class ReportWriter {

  String render(String format, byte[] data, String path) {
    if (format.equals("csv")) { // fixed: string-equality-check
      data = toCsv(data);
    }
    try (FileOutputStream out = newStream(path)) { // fixed: resource-leak
      out.write(data);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    return "ok";
  }

  void load(String path) {
    try {
      readAll(path);
    } catch (IOException e) {
      throw new RuntimeException(e); // fixed: empty-catch-block
    }
  }

  byte[] toCsv(byte[] d) {
    return d;
  }

  FileOutputStream newStream(String p) throws IOException {
    return null;
  }

  void readAll(String p) throws IOException {}
}
