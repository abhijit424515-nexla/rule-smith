import java.io.Serializable;

class Engine implements Serializable {
  int horsepower;
}

class Car implements Serializable {
  private Engine engine;
  private int wheels;
}
