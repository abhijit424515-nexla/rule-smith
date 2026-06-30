public class Loader {
  Object run(String cls) throws Exception {
    Class<?> c = Class.forName(cls);
    return c.getDeclaredConstructor().newInstance();
  }
}
