import java.lang.reflect.Field;

public class Peek {
  Object read(Object o) throws Exception {
    Field f = o.getClass().getDeclaredField("secret");
    f.setAccessible(true);
    return f.get(o);
  }
}
