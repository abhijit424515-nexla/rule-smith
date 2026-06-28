public class Test {
    public void process() {
        try {
            doWork();
        } catch (Exception e) {
            logger.error("Failed", e);
        }
    }
}