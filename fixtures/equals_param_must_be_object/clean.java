public class User {
  final String id;

  User(String id) {
    this.id = id;
  }

  @Override
  public boolean equals(Object o) {
    if (!(o instanceof User)) {
      return false;
    }
    return id.equals(((User) o).id);
  }
}
