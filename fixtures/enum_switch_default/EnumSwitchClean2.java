class EnumSwitchClean2 {
  void process(Type t) {
    switch (t) {
      case TYPE_A:
        handleA();
        break;
      case TYPE_B:
        handleB();
        break;
      case TYPE_C:
        handleC();
        break;
      default:
        handleDefault();
    }
  }
}
