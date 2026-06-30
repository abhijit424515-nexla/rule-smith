import java.math.BigDecimal;

public class CleanValueOf {
  public BigDecimal rate() {
    BigDecimal a = BigDecimal.valueOf(0.1);
    BigDecimal b = new BigDecimal(10);
    return a.add(b);
  }
}
