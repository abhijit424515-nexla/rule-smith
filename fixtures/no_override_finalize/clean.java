public class Resource implements java.io.Closeable {
    private java.io.InputStream stream;

    @Override
    public void close() throws java.io.IOException {
        if (stream != null) {
            stream.close();
        }
    }
}
