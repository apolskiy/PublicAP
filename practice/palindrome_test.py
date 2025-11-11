"""Alex polskiy following function is a palindrome test
from operator import truediv"""


def palindrome(full_string :str) -> bool:
    """palindrome function returns TRUE if the string is a palindrome, FALSE otherwise"""
    if full_string == full_string[::-1]:
        return True

    return False


if __name__ == "__main__":
    print(palindrome("racecar"))
    print(palindrome("hello"))
    print(palindrome("A man, a plan, a canal, Panama!"))
    print(palindrome("12321"))
    print(palindrome("12345"))
