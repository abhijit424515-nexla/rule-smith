import javax.script.ScriptEngine;

public class CleanScript {
  void run(ScriptEngine engine) throws Exception {
    engine.eval("1 + 1");
  }
}
