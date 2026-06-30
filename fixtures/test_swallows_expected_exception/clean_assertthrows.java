import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.Test;

class BazTest {
  @Test
  public void shouldThrowOnBadInput() {
    assertThrows(IllegalArgumentException.class, () -> parse("bad"));
  }
}
