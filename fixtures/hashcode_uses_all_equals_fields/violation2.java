public class Person {
  private String name;
  private int age;

  @Override
  public boolean equals(Object o) {
    if (!(o instanceof Person)) return false;
    Person other = (Person) o;
    return name.equals(other.name) && age == other.age;
  }

  @Override
  public int hashCode() {
    return name.hashCode();
  }
}
