"""This experimental_tests returns maximum area of water in container"""
class ContainerBox:
    """This class represents a ContainerBox to the container with most water problem,
    where height of the container is represented by a list of integers and length
    is the distance between integers in the list"""
    def __init__(self,value=0):
        print("Initializing ContainerBox object")
        self.area = value
    def maxArea(self, height: list[int])->int:
        """This function finds two lines that together with x-axis form a container such
        that the container contains most water and returns the maximum amount of water
        the container may store"""
        maxarea,left,right = 0,0,len(height) - 1

        while left < right:
            area = min(height[left], height[right]) * (right - left)
            maxarea = max(maxarea, area)

            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        return maxarea

    def print_area(self) -> None:
        """Prints the maximum area of water that can be stored in the container,
        which is stored in the self.area attribute of the ContainerBox object."""
        print(f"Maximum Water the container can store is: {self.area}")


if __name__ == "__main__":
    lines = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    container = ContainerBox(0)
    print(f"Max water in the container {container.maxArea(lines)}")
    #container.print_area()
    lines = [1, 1]
    container2 = ContainerBox(0)
    container2.maxArea(lines)
    print(f"Max water in the container {container2.maxArea(lines)}")
    #container2.print_area()
