"""Alex Polskiy this script converts roman numbers to arabic"""
import unittest
def roman_to_arabic(roman: str) ->int:
    """This function converts roman numbers to arabic"""
    print("Entered function roman_to arabic \n")

    temp = roman.upper()

    #print(f"Temp: {temp}. Length: {len(temp)}\n")
    arabic=0

    if len(temp) < 1 or len(temp) > 15:
        return arabic


    roman_numerals = {"M":1000,"CM":900, "D":500, "C":100,"L":50, "X":10,"V":5,"I":1}

    for letter in range(len(temp) - 1):
        if roman_numerals[temp[letter]] < roman_numerals[temp[letter+1]]:
            # If current is less than the next, it's a subtractive case
            arabic -= roman_numerals[temp[letter]]
        else:
            arabic += roman_numerals[temp[letter]]
    # Add the value of the last character, which is always added
    arabic += roman_numerals[temp[-1]]
    return arabic

class ConvertToArabic(unittest.TestCase):
    """This unittest class tests conversion of roman numbers to arabic"""
    def test_r_to_a_III(self):
        num="III"
        self.assertEqual(roman_to_arabic(num),3)

    def test_r_to_a_LVIII(self):
        num="LVIII"
        self.assertEqual(roman_to_arabic(num),58)

    def test_r_to_a_MCMXCIV(self):
        num="MCMXCIV"
        self.assertEqual(roman_to_arabic(num),1994)

if __name__ == "__main__":
    unittest.main()


