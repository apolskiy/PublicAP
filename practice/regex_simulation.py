import re
class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        found = False
        if not "*" in p and not "." in p:
            return s == p
        else:
            pattern = r"{}".format(p)
            found = bool(re.fullmatch(pattern, s))
            return found

if __name__ == "__main__":
    s ="aa"
    p ="a*"
    print(Solution().isMatch(s, p))
    s ="aab"
    p ="c*a*b"
    print(Solution().isMatch(s, p))
    s ="mississippi"
    p ="mis*is*p*."
    print(Solution().isMatch(s, p))
    s ="mississippi"
    p ="mis*is*ip*."
    print(Solution().isMatch(s, p))

    s ="abcd"
    p ="d*"

    print(Solution().isMatch(s, p))

    s ="aaa"
    p ="a.a"
    print(Solution().isMatch(s, p))

    s="aaa"
    p=".a"
    print(Solution().isMatch(s, p))
    p=".*.."
    s="ab"
    print(Solution().isMatch(s, p))
    p="c*."
    s="a"
    print(Solution().isMatch(s, p))
