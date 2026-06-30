import org.junit.Test;

class FooTest {
  @Test
  public void shouldThrowOnBadInput() {
    try {
      parse("bad");
    } catch (IllegalArgumentException e) {
      // expected
    }
  }
}
