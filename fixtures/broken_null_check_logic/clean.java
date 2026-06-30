public class UserGateOk {
  public boolean isInactive(String name) {
    if (name != null && name.isEmpty()) {
      return true;
    }
    return false;
  }
}
