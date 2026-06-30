import javax.annotation.concurrent.Immutable;

@Immutable
public final class Matrix {
  private final int[] data;

  Matrix(int[] data) {
    this.data = data;
  }

  int[] data() {
    return this.data;
  }
}
