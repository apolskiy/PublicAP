"""Aleksandr Polskiy following script does atoi translation for signed ints only"""
import unittest
def tempreturn(num) -> int:
    """This function returns the number if it is within the bounds
     of a 32-bit signed integer, otherwise it returns the maximum or minimum value."""
    if num > (2 ** 31 - 1):
        return (2 ** 31 - 1)
    elif num < (-2 ** 31):
        return (-2 ** 31)
    else:
        return num

def myAtoi(s: str) -> int:
    """This function converts a string to an integer."""
    sign = 1 #defaulting sign to positive
    loc = 0 #defaulting location to start of string

    temp = 0 #temporary number that will be calculated and returned

    s = s.strip(" ")
    length = len(s)
    if length > 200:
        return 0
    print(f"String {s} length {length}")
    if s.startswith("-"):
        sign = -1
        loc += 1
    elif s.startswith("+"):
        sign = 1
        loc += 1

    #This loop cycles through each character on the string after the
    #whitespace removal and adjustment for sign, as soon as non numeric character is encountered
    #temp is returned
    for counter in range(loc, length):
        if s[counter].isdecimal():
            temp = temp * 10 + int(s[counter])
        else:
            break
    return tempreturn(temp * sign)
class Testatoi_for_string(unittest.TestCase):
    def test_atoi_for_stringhello(self):
        self.assertEqual(myAtoi("hello"), 0)

    def test_atoi_for_stringn42(self):
        self.assertEqual(myAtoi("-042"), -42)

    def test_atoi_for_string20(self):
        self.assertEqual(myAtoi("20"), 20)

    def test_atoi_for_stringp1(self):
        self.assertEqual(myAtoi("+1"), 1)

    def test_atoi_for_stringnlargerthansignint(self):
        self.assertEqual(myAtoi("-934059853282357821735"), -2 ** 31)
if __name__ == "__main__":
    unittest.main()
