class ItemService {
  int countItems(java.util.List<String> xs) {
    return xs.size();
  }

  boolean hasItems(java.util.List<String> xs) {
    return xs.size() > 0;
  }
}
