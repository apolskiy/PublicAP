"""This function takes in an array/list of integers
and returns missing number, from the pattern"""
import unittest
from typing import List

def missingNumber(nums: List[int]) -> int:
    """This function takes a list of integers and returns
    missing number from the pattern"""
    if len(nums) == 1:
        if nums[0] == 1:
            return 0
        else:
            return nums[0] + 1
    if len(nums) == 0:
        return 0
    if len(nums) > 1:
        full_range = set(range(0, max(nums) + 1))
        print(f" Full Range: {full_range}")

        if full_range != set(nums):
            missing_numbers = full_range - set(nums)
        else:
            return max(nums) + 1
    if len(missing_numbers) > 0:
        answer = int(missing_numbers.pop())
        print(f" Missing Numbers: {answer}")
        return answer
    return 0


class TestMissingNumber(unittest.TestCase):
    def test_missing_number_three_numbers(self):
        """Test case for missing number from the middle,
        with three numbers around"""
        self.assertEqual(missingNumber([3, 0, 1]), 2)

    def test_missing_number_empty_list(self):
        """Test case for empty list, should return 0"""
        self.assertEqual(missingNumber([]), 0)

    def test_missing_number_single_number(self):
        """Test case for single number 0,
        should return next number"""
        self.assertEqual(missingNumber([0]), 1)

    def test_missing_number_zero(self):
        """Test case for single number 1,
        should return 0"""
        self.assertEqual(missingNumber([1]), 0)

    def test_missing_number_multiple_missing(self):
        self.assertEqual(missingNumber([9, 6, 4, 2, 3, 5, 7, 0, 1]), 8)

    def test_missing_number_two_numbers(self):
        self.assertEqual(missingNumber([0, 1]), 2)

if __name__ == '__main__':
    unittest.main()