"""Following script uses hash for O(n) solution
of sum of two numbers in a list equal to target number
and returns indices of first found numbers that make the sum"""
import unittest


def two_sum_indices(nums:list, target:float)->list:
    """This is  list of numbers which is evaluated
    for target sum. If match is found indices of
    those numbers in the list are returned"""
    # Create a hash map to store numbers and their indices
    seen_nums = {}

    # Iterate through the array with index and value
    for index, number in enumerate(nums):
        complement = target - number
        # Check if the complement is already in the hash map
        if complement in seen_nums:
            # If found, return the complement's index and the current index
            return [seen_nums[complement]+1, index+1]

        # If not, add the current number and its index to the hash map
        seen_nums[number] = index

    # Per problem constraints, a solution is guaranteed, but this is a fallback
    return []

class TestSumTwoNumbers(unittest.TestCase):
    def test_two_nums(self):
        response = two_sum_indices([7, 2, 11, 5], 9)
        expected = [1,2]
        assert  response ==expected,f"Failed got {response} and expected {expected}"

    def test_0_1_9(self):
        response = two_sum_indices([7, 2, 9, 4, 3, 5, 6, 8, 3, 3], 9)
        expected = [1,2]
        assert  response ==expected,f"Failed got {response} and expected {expected}"

    def test_0_6_6(self):
        response = two_sum_indices([0, 7, 9, 4, 3, 5, 6, 8, 3, 3], 6)
        expected=[1,7]
        assert  response ==expected,f"Failed got {response} and expected {expected}"

    def test_10_empty(self):
        response = two_sum_indices([0, 3, 8, 6, 1, 5, 6, 8, 3, 3], 10)
        expected = []

        assert response == expected, f"Failed got {response} and expected {expected}"

if __name__ == "__main__":
    unittest.main()

