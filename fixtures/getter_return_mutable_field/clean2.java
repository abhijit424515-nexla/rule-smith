import java.util.Arrays;

public class Buffer {
  private byte[] data;
  private String label;

  public byte[] getData() {
    return Arrays.copyOf(data, data.length);
  }

  public String getLabel() {
    return label;
  }
}
