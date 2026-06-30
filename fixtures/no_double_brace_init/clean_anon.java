import java.util.ArrayList;
import java.util.List;

public class CleanAnon {
  private final List<String> items = new ArrayList<>();

  {
    items.add("init");
  }

  public Runnable make() {
    return new Runnable() {
      @Override
      public void run() {
        System.out.println("hi");
      }
    };
  }
}
