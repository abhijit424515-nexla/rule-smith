public final class Email {
  private final String value;

  private Email(String value) {
    this.value = value;
  }

  public static Email of(String value) {
    if (value == null || value.isEmpty()) {
      throw new IllegalArgumentException("invalid email");
    }
    return new Email(value);
  }
}
