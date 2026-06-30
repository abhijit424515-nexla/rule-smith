import java.io.Serializable;

class Address {
  String street;
}

class Person implements Serializable {
  private String name;
  private Address address;
}
