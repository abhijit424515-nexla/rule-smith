import java.util.AbstractList;

class ReadOnly extends AbstractList<String> {
  @Override
  public String get(int index) {
    return "fixed";
  }

  @Override
  public int size() {
    return 1;
  }

  @Override
  public boolean add(String item) {
    throw new UnsupportedOperationException("Immutable collection does not support add");
  }
}
