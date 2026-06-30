public class Address {
  private String street;
  private String city;
  private String zip;
  private String country;

  public String full() {
    return street + " " + city + " " + zip + " " + country;
  }
}
