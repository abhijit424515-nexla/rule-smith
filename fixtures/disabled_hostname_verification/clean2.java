import javax.net.ssl.HttpsURLConnection;

public class Clean2 {
  void open(HttpsURLConnection c) throws Exception {
    c.connect();
  }
}
