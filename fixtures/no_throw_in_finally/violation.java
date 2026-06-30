class A {
    void f() {
        try {
            work();
        } finally {
            throw new IllegalStateException("cleanup failed");
        }
    }
}
