public class Handle {
    protected void finalize() {
        System.out.println("cleanup");
    }
}
