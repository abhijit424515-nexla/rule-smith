import java.util.Map;

public class Indexer {
  void buildIndex(Iterable<Doc> docs, Map<String, Doc> sink) {
    for (Doc d : docs) {
      sink.put(d.id(), d);
    }
  }
}
