public class Builder {
  private String result;

  // Not an override of Object.finalize(): it takes a parameter.
  public String finalize(String suffix) {
    result = suffix;
    return result;
  }
}
