import org.springframework.expression.spel.standard.SpelExpressionParser;

public class CleanSpel {
  Object compute(SpelExpressionParser parser) {
    String expr = "a + b";
    return parser.parseExpression(expr).getValue();
  }
}
