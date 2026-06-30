import java.lang.reflect.Proxy;

public class Wiring {
  Object make(ClassLoader cl, Class<?>[] ifaces, java.lang.reflect.InvocationHandler h) {
    return Proxy.newProxyInstance(cl, ifaces, h);
  }
}
