import javax.servlet.http.HttpServletRequest;
import org.springframework.expression.spel.standard.SpelExpressionParser;

public class EvalSpel {
  Object run(HttpServletRequest req, SpelExpressionParser parser) {
    String q = req.getParameter("expr");
    return parser.parseExpression(q).getValue();
  }
}
