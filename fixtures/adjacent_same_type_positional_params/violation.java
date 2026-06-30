public class Geo {
  public double distance(double srcLat, double srcLon, double dstLat, double dstLon) {
    return Math.hypot(dstLat - srcLat, dstLon - srcLon);
  }
}
