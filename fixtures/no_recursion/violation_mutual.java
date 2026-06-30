public class PingPong {
  boolean ping(int n) {
    if (n == 0) {
      return true;
    }
    return pong(n - 1);
  }

  boolean pong(int n) {
    if (n == 0) {
      return false;
    }
    return ping(n - 1);
  }
}
