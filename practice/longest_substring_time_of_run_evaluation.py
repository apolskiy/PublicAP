from timeit import timeit
#longest substring with non-repeating letters
def lengthOfLongestSunstring(s: str)-> int:
    substring = ""

    tlongest = 0
    for letter in s:
        if not letter in substring:
            substring+=letter
            if len(substring) > tlongest:
                tlongest = len(substring)

        elif letter in substring:
            substring = letter


        else:
            print(f"Error {letter} has created problems with the script")

    return tlongest


if __name__ == "__main__":
    execution_time = timeit(lambda: lengthOfLongestSunstring("abcabcbb"), number=10000)
    print(f"Average execution time: {execution_time / 10000:.6f} seconds per run. Result: {lengthOfLongestSunstring('abcabcbb')}")

    execution_time = timeit(lambda: lengthOfLongestSunstring("bbbbb"), number=10000)
    print(f"Average execution time: {execution_time / 10000:.6f} seconds per run. Result: {lengthOfLongestSunstring('bbbbb')}")

    execution_time = timeit(lambda: lengthOfLongestSunstring("pwwkew"), number=10000)
    print(f"Average execution time: {execution_time / 10000:.6f} seconds per run. Result: {lengthOfLongestSunstring('pwwkew')}")

    execution_time = timeit(lambda: lengthOfLongestSunstring("abcabcdebb"), number=10000)
    print(f"Average execution time: {execution_time / 10000:.6f} seconds per run. Result: {lengthOfLongestSunstring('abcabcdebb')}")



