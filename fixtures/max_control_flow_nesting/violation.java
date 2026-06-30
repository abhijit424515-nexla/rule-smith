class Sample {
  void deep(int[][] grid) {
    if (grid != null) {
      for (int i = 0; i < grid.length; i++) {
        while (i < 10) {
          if (grid[i] != null) {
            for (int j = 0; j < grid[i].length; j++) {
              System.out.println(grid[i][j]);
            }
          }
          i++;
        }
      }
    }
  }
}
