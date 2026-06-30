class A {
    void m(int x) {
        switch (x) {
            case 1:
            case 2:
                foo();
                break;
            case 3:
                return;
            default:
                throw new RuntimeException();
        }
    }
}
