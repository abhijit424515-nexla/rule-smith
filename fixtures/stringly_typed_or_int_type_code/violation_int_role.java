public class Auth {
  boolean canEdit(int userRole) {
    if (userRole == 2) {
      return true;
    }
    return false;
  }
}
