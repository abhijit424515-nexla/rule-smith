public class User {
  private final String name;
  private final int age;
  private final boolean active;

  public User(String name, int age, boolean active) {
    this.name = name;
    this.age = age;
    this.active = active;
  }

  public String getName() {
    return name;
  }
}
