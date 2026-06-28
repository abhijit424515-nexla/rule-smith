class Example {
    enum Status { ON, OFF }
    
    void handle(Status status) {
        switch(status) {
            case ON:
                doOn();
                break;
            case OFF:
                doOff();
                break;
            default:
                throw new IllegalStateException();
        }
    }
}