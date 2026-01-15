"""Aleksandr Polskiy practice of finding a concatenation of a substring list in a string.
Substring consists of a list of words all equal length, where substring can be concatenated
in various permutations
Probem is solved using sliding window the size of all substrings
put together, sliding along the target string"""

from collections import Counter, defaultdict
from typing import List
import unittest


def findSubstring(s: str, words: List[str]) -> List[int]:
    """This function finds a substring that is a concatenation of words from the words list
    inside a string"""
    if not s or not words:
        return []

    wlen = len(words[0])
    allwordslen = len(words)
    total_len = wlen * allwordslen
    slen = len(s)

    if total_len > slen:
        return []

    need = Counter(words)
    result = []

    for offset in range(wlen):
        left = offset
        found = defaultdict(int)
        used = 0

        for right in range(offset, slen - wlen + 1, wlen):
            word = s[right:right + wlen]

            if word not in need:
                found.clear()
                used = 0
                left = right + wlen
                continue

            found[word] += 1
            used += 1

            while found[word] > need[word]:
                left_word = s[left:left + wlen]
                found[left_word] -= 1
                used -= 1
                left += wlen

            if used == allwordslen:
                result.append(left)
                left_word = s[left:left + wlen]
                found[left_word] -= 1
                used -= 1
                left += wlen

    return result

#Class to run unit tests
class TestSubstring(unittest.TestCase):
    """Class to run unit tests for findSubstring function"""
    def test_findSubstring3words21letters(self):
        st = "barfoofoobarthefoobarman"
        wordlist = ["bar", "foo", "the"]
        expected = [6, 9, 12]
        self.assertEqual(findSubstring(s=st, words=wordlist), expected)

    def test_findSubstring2words12letters(self):
        st = "foobarfoobar"
        wordlist = ["foo", "bar"]
        expected = [0, 3, 6]
        self.assertEqual(findSubstring(s=st, words=wordlist), expected)

    def test_findSubstring2_1letterwords3letters(self):
        st = "abcabcabc"
        wordlist = ["a", "b", "c"]
        expected = [0,1,2,3,4,5,6]
        self.assertEqual(findSubstring(s=st, words=wordlist), expected)

    def test_failfindSubstring20oneletterwords31letters(self):
        st = "fffffffffffffffffffffffffffffffff"
        wordlist = ["a"] * 20
        expected = []
        self.assertEqual(findSubstring(s=st, words=wordlist), expected)

    def test_failfindSubstring30words1800letters(self):
        st = ("pjzkrkevzztxductzzxmxsvwjkxpvukmfjywwetvfnujhweiybwvvsrfequzkh"
              "ossmootkmyxgjgfordrpapjuunmqnxxdrqrfgkrsjqbszgiqlcfnrpjlcwdrvb"
              "umtotzylshdvccdmsqoadfrpsvnwpizlwszrtyclhgilklydbmfhuywotjmktn"
              "wrfvizvnmfvvqfiokkdprznnnjycttprkxpuykhmpchiksyucbmtabiqkisgbhx"
              "ngmhezrrqvayfsxauampdpxtafniiwfvdufhtwajrbkxtjzqjnfocdhekumttuq"
              "wovfjrgulhekcpjszyynadxhnttgmnxkduqmmyhzfnjhducesctufqbumxbamal"
              "qudeibljgbspeotkgvddcwgxidaiqcvgwykhbysjzlzfbupkqunuqtraxrlptiv"
              "shhbihtsigtpipguhbhctcvubnhqipncyxfjebdnjyetnlnvmuxhzsdahkrscewa"
              "bejifmxombiamxvauuitoltyymsarqcuuoezcbqpdaprxmsrickwpgwpsoplhugb"
              "ikbkotzrtqkscekkgwjycfnvwfgdzogjzjvpcvixnsqsxacfwndzvrwrycwxrcismd"
              "hqapoojegggkocyrdtkzmiekhxoppctytvphjynrhtcvxcobxbcjjivtfjiwmduhz"
              "jokkbctweqtigwfhzorjlkpuuliaipbtfldinyetoybvugevwvhhhweejogrghlls"
              "ouipabfafcxnhukcbtmxzshoyyufjhzadhrelweszbfgwpkzlwxkogyogutscvuhc"
              "llphshivnoteztpxsaoaacgxyaztuixhunrowzljqfqrahosheukhahhbiaxqzfmmw"
              "cjxountkevsvpbzjnilwpoermxrtlfroqoclexxisrdhvfsindffslyekrzwzqkpeo"
              "cilatftymodgztjgybtyheqgcpwogdcjlnlesefgvimwbxcbzvaibspdjnrpqtyeil"
              "kcspknyylbwndvkffmzuriilxagyerjptbgeqgebiaqnvdubrtxibhvakcyotkfonm"
              "seszhczapxdlauexehhaireihxsplgdgmxfvaevrbadbwjbdrkfbbjjkgcztkcbwag"
              "tcnrtqryuqixtzhaakjlurnumzyovawrcjiwabuwretmdamfkxrgqgcdgbrdbnugze"
              "cbgyxxdqmisaqcyjkqrntxqmdrczxbebemcblftxplafnyoxqimkhcykwamvdsxjezk"
              "pgdpvopddptdfbprjustquhlazkjfluxrzopqdstulybnqvyknrchbphcarknnhhovw"
              "eaqawdyxsqsqahkepluypwrzjegqtdoxfgzdkydeoxvrfhxusrujnmjzqrrlxglcmkiy"
              "kldbiasnhrjbjekystzilrwkzhontwmehrfsrzfaqrbbxncphbzuuxeteshyrveamjsf"
              "iaharkcqxefghgceeixkdgkuboupxnwhnfigpkwnqdvzlydpidcljmflbccarbiegsmwe"
              "klwngvygbqpescpeichmfidgsjmkvkofvkuehsmkkbocgejoiqcnafvuokelwuqsgkyoe"
              "karoptuvekfvmtxtqshcwsztkrzwrpabqrrhnlerxjojemcxel")

        wordlist = ["dhvf", "sind", "ffsl", "yekr", "zwzq", "kpeo", "cila", "tfty", "modg", "ztjg", "ybty", "heqg",
                    "cpwo", "gdcj", "lnle", "sefg", "vimw", "bxcb"]

        expected = [935]
        self.assertEqual(findSubstring(s=st, words=wordlist), expected)


if __name__ == "__main__":
    unittest.main()


