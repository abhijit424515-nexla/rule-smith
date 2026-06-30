public class Buffer {
  private byte[] data = new byte[16];
  private int dataSize;

  public void write(byte b) {
    data[dataSize] = b;
    dataSize++;
  }
}
