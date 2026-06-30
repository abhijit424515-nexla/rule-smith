class EnumSwitchViolation2 {
  void process(Status s) {
    switch (s) {
      case ACTIVE:
        handleActive();
        break;
      case INACTIVE:
        handleInactive();
        break;
    }
  }
}
