"""Alex Polskiy following function is a palindrome high performance
test without using string operations"""
class Palindrome:
    """class palindrome defines high performance object"""
    def ispalindrome(self, x: int) -> bool:
        """This function checks if the integer is a palindrome.
        Declaring all temp variables outside the loop,
        to increase performance."""
        rx = 0
        tx = x
        digit = None
        #If basic conditions fail no need to do any further processing
        #False is returned
        if x < 0 or (x%10==0 and x!=0):
            return False
        # if basic conditions pass proceed with palindrome check
        # original variable is stored in tx reverse number is stored in rx

        while tx > 0:
            digit = tx % 10
            rx = (rx*10)+digit
            tx = tx // 10
        return x == rx
    def print_result(self,x: int) -> None:
        """Prints the result of the palindrome check for a given integer."""
        print(f"Is {x} a palindrome? {self.ispalindrome(x)}")

if __name__ == "__main__":

    Palindrome().print_result(12321)
    Palindrome().print_result(12345)
    Palindrome().print_result(123321)
    Palindrome().print_result(12332000000)
    print(Palindrome().ispalindrome(1))
    print(Palindrome().ispalindrome(0))
    print(Palindrome().ispalindrome(12332135709387508302748503274503720457430750))
    print(Palindrome().ispalindrome(12345678987654321))
    print(Palindrome().ispalindrome(1234567898765432112345678987654321))
    print(Palindrome().ispalindrome(123456789987654323456789123456789857463521))
