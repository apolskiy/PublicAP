#Alex polskiy following function is a palindrome test
from operator import truediv


#Function returns TRUE if the string is a palindrome, FALSE otherwise
def palindrome(full_string :str) -> bool:
    if full_string == full_string[::-1]:
        return True
    else:
        return False


if __name__ == "__main__":
    print(palindrome("racecar"))
    print(palindrome("hello"))
    print(palindrome("A man, a plan, a canal, Panama!"))
    print(palindrome("12321"))
    print(palindrome("12345"))