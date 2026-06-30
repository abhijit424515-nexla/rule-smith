public class NotAnIterator {
  static class Node {
    Node next;
    int val;
  }

  private Node head;

  public Node next(Node n) {
    return n.next;
  }

  public int size() {
    int c = 0;
    for (Node n = head; n != null; n = n.next) {
      c++;
    }
    return c;
  }
}
