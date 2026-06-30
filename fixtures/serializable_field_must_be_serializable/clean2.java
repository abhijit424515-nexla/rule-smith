import java.io.Serializable;

class Address {
  String street;
}

class Person implements Serializable {
  private String name;
  private transient Address address;
  private static Address shared;
}
