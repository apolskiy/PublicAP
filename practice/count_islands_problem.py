"""Aleksandr Polskiy count islands problem a matrix is given
interconnected 1s are considered islands, 0 are considered water
count the number of islands on a 2d grid"""

def num_islands(grid) -> int:
    """This function counts the number of islands on a 2d grid"""
    if not grid or not grid[0]:
        return 0

    rows = len(grid)
    cols = len(grid[0])
    count = 0

    def depth_first_search(r, c):
        """This function looks at cells in rows above, below and columns
        to the right and to the left of the current cell"""
        # Base cases for recursion termination
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return

        # Mark the cell as visited by changing '1' to '0' (or any other marker)
        # We need to use a mutable type like a list of lists if we modify the grid in place
        # In a real problem, it's better to use a visited set if you can't modify the input
        grid[r][c] = '0'

        # Explore all four directions
        depth_first_search(r + 1, c)  # Down
        depth_first_search(r - 1, c)  # Up
        depth_first_search(r, c + 1)  # Right
        depth_first_search(r, c - 1)  # Left

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                depth_first_search(r, c)

    return count

if __name__ == "__main__":
    print(num_islands([["1","1","1","1","0"],
                      ["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]))
    print(num_islands([["1","1","0","0","0"],
                      ["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]))
    print(num_islands([["1","0","1","0","1"],
                      ["0","1","0","1","0"],["1","0","1","0","1"],["0","1","0","1","0"]]))
    print(num_islands(
        [["0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0"],
         ["0", "0", "0", "0", "0"], ["0", "0", "0", "0", "0"]]))
