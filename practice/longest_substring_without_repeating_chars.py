#Alex Polskiy practice. Find the longest substring without repeating characters.
"""This script finds the logest substring without repetitions"""

def length_of_longest_non_repeating_substring(full_string: str) -> int:
    char_set = set()
    location = 0
    max_length = 0
    #length_full_string = len(full_string)

    for spot in range(len(full_string)):
        # Shrink the window if a duplicate is found
        while full_string[spot] in char_set:
            char_set.remove(full_string[location])
            location += 1

        # Expand the window and update max length
        char_set.add(full_string[spot])
        current_length = spot - location + 1
        max_length = max(max_length, current_length)

    return max_length

print(length_of_longest_non_repeating_substring("abscabcabcabcdabcde"))
print(length_of_longest_non_repeating_substring("abcabcabc"))
print(length_of_longest_non_repeating_substring("bbbbb"))
print(length_of_longest_non_repeating_substring("pwwkew"))
print(length_of_longest_non_repeating_substring(" "))
print(length_of_longest_non_repeating_substring(""))