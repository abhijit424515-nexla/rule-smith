class B {
    void g(boolean bad) throws Exception {
        try {
            work();
        } catch (Exception e) {
            log(e);
        } finally {
            if (bad) {
                throw new RuntimeException("bad state");
            }
        }
    }
}
