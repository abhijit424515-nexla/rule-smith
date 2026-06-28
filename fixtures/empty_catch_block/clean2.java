public class Test {
    public void process() {
        try {
            doWork();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}