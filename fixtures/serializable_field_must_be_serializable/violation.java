import java.io.Serializable;

class Engine {
  int horsepower;
}

class Car implements Serializable {
  private Engine engine;
  private int wheels;
}
