package examples;

import java.io.FileOutputStream;
import java.io.IOException;

public class ReportWriter {

  String render(String format, byte[] data, String path) {
    if (format == "csv") { // string-equality-check
      data = toCsv(data);
    }
    FileOutputStream out = newStream(path); // resource-leak: never closed
    out.write(data);
    return "ok";
  }

  void load(String path) {
    try {
      readAll(path);
    } catch (IOException e) {
    } // empty-catch-block: swallowed
  }

  byte[] toCsv(byte[] d) {
    return d;
  }

  FileOutputStream newStream(String p) {
    return null;
  }

  void readAll(String p) throws IOException {}
}
