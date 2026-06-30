import static org.junit.Assert.fail;

import org.junit.Test;

class FooTest {
  @Test
  public void shouldThrowOnBadInput() {
    try {
      parse("bad");
      fail("expected IllegalArgumentException");
    } catch (IllegalArgumentException e) {
      // expected
    }
  }
}
