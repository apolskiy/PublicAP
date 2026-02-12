"""Aleksandr Polskiy calculating product of all array
values except for current value
and return resulting array"""

def product_except_self(nums: list[int]) -> list:
    """This function receives array/list of numbers as input and returns
    a list of product of all numbers except current value"""
    length_nums = len(nums)
    res = [1] * n

    # Left Pass: Calculate prefix products
    prefix = 1
    for item in range(length_nums):
        res[item] = prefix
        prefix *= nums[item]

    # Right Pass: Calculate suffix(after the number) products and combine
    suffix = 1
    for item in range(length_nums - 1, -1, -1):
        res[item] *= suffix
        suffix *= nums[item]

    return res

if __name__ == "__main__":
    print(product_except_self([1,2,3,4]))
    print(product_except_self([1,2,0,4]))
    print(product_except_self([0,0,0,0]))
    print(product_except_self([1,0,2,0]))
    print(product_except_self([0,1,2,3]))
    print(product_except_self([-1,-2,-3,-4]))
    print(product_except_self([1,1,1,1,1]))