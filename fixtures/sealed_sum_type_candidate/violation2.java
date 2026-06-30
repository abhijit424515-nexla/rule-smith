public class Notification {
  private int status;
  private String emailBody;
  private String smsText;
  private String pushPayload;

  public String render() {
    if (status == 1) {
      return emailBody;
    } else if (status == 2) {
      return smsText;
    } else {
      return pushPayload;
    }
  }
}
