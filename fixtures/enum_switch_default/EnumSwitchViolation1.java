class Test {
    enum Color { RED, BLUE, GREEN }
    
    void test(Color c) {
        switch(c) {
            case RED:
                System.out.println("red");
                break;
            case BLUE:
                System.out.println("blue");
                break;
        }
    }
}