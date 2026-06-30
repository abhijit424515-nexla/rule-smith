import java.util.Comparator;

public class Registry {
  private final Object key = new Object();

  @Override
  public boolean equals(Object o) {
    Runnable r =
        () -> {
          throw new RuntimeException("belongs to the lambda, not equals");
        };
    Comparator<String> c =
        new Comparator<String>() {
          @Override
          public int compare(String a, String b) {
            throw new IllegalStateException("belongs to compare, not equals");
          }
        };
    return this == o;
  }
}
