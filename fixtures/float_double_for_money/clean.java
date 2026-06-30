import java.math.BigDecimal;

public class Invoice {
  public BigDecimal computeTotal(int qty) {
    BigDecimal price = new BigDecimal("19.99");
    return price.multiply(BigDecimal.valueOf(qty));
  }
}
