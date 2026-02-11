"""Alex Polskiy this script converts arabic numbers to roman"""
import unittest

def int_To_Roman(num: int) -> str:
    """This function converts arabic numbers to roman"""
    #Dictionary roman_numerals contains all roman numbers,
    # including special exceptions CM, CD, XC, XL, IX and IV
    roman_numerals = {"M":1000,"CM":900, "D":500,"CD":400, "C":100,
                      "XC":90,"L":50,"XL":40, "X":10,"IX":9,"V":5, "IV":4,"I":1}
    temp = num
    roman = ""
    #If arabic number is 0 returns, empty string,
    # as romans had no concept of 0 or negative numbers
    if not num > 0:
        return ""

    #going through the dictionary and evaluating
    #floor division
    for letter, value in roman_numerals.items():
        count = temp//value
        if (temp>0) and (count > 0):
            for i in range(0, count):
                roman += letter
                #print(roman + "\n")
                temp -= value
                if not temp > 0:
                    return roman
    print(f"final roman number: {roman}")
    return roman

class ConvertToRoman(unittest.TestCase):
    """This class tests conversion of arabic numbers to roman"""
    def test_ator_3749(self):
        """Converting 3749 to roman"""
        totest=3749
        test = int_To_Roman(totest)
        self.assertEqual(test,"MMMDCCXLIX")

    def test_ator_58(self):
        """Converting 58 to roman"""
        totest=58
        test = int_To_Roman(totest)
        self.assertEqual(test,"LVIII")

    def test_ator_1994(self):
        """Converting 1994 to roman"""
        totest=1994
        test = int_To_Roman(totest)
        self.assertEqual(test,"MCMXCIV")

    def test_ator_0(self):
        """Converting 0 to roman, should not convert"""
        totest=0
        test = int_To_Roman(totest)
        self.assertEqual(test,"")

if __name__ == '__main__':
    unittest.main()
    