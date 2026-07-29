"""Aleksandr Polskiy this script searches a string under 1000
characters for palindromic substrings and returns the longest one"""
#Approach

def longestPalindrome(self, s: str) -> str:
    if not s or len(s) > 1000:
        return ""
    start = 0
    max_len = 1
    lens = len(s)

    def expandAroundMiddle(left: int, right: int) -> tuple[int, int]:
        while left >= 0 and right < lens and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right - 1

    for index in range(lens):
        # check for palindromes center at i
        l, r = expandAroundMiddle(index, index)
        if r - l + 1 > max_len:
            start = l
            max_len = r - l + 1
        # check for palindromes center between i and i+1
        l, r = expandAroundMiddle(index, index + 1)
        if r - l + 1 > max_len:
            start = l
            max_len = r - l + 1
    return s[start:start + max_len]