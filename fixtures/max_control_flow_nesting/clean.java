class Sample {
  void shallow(int[][] grid) {
    if (grid != null) {
      for (int i = 0; i < grid.length; i++) {
        while (i < 10) {
          if (grid[i] != null) {
            System.out.println(grid[i].length);
          }
          i++;
        }
      }
    }
  }
}
