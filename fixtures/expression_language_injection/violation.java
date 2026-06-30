import javax.script.ScriptEngine;

public class EvalScript {
  void run(ScriptEngine engine, String userInput) throws Exception {
    engine.eval(userInput);
  }
}
