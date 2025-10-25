import re


def count_consecutive_letters(text):
    """
    Finds and counts all instances of 4 or more of the same consecutive letters.

    takes Args:
        text (str): The input string to search.

    Returns:
        dict: A dictionary with the letters as keys and their counts of the numbers of multiple occurrences as values.
    """
    # Initialize an empty dictionary to store the counts.
    counts = {}

    # Regex pattern explanation:
    # r'([a-zA-Z])' - Matches and captures any single letter (both cases).
    # \1{3,}      - A backreference that matches the captured letter (\1) 3 or more times.
    # The entire pattern together finds the captured letter repeated at least 4 times in total.
    pattern = r'([agtcAGTC])\1{3,}'

    # Use re.finditer to find all non-overlapping matches and their details.
    for match in re.finditer(pattern, text):
        # The captured letter is in group 1 of the match object.
        letter = match.group(1)

        # The full matching string contains the sequence of repeated letters.
        full_match = match.group(0)

        # The length of the full match is the number of consecutive letters.
        length = len(full_match)

        # Update the dictionary. Each unique sequence (e.g., 'aaaa' vs 'bbbbb') is a different count.
        if letter in counts:
            counts[letter] += 1
        else:
            counts[letter] = 1

    return counts


# Example usage with a sample string
sample_text = "ACGTGCTTTTTGGAAACTCCCAAAAATTTTCCCCCTTTTTAAAGGTCTAGATGTCAGTCTGCTGATTTCCCCTTAAAAAGGGGGTTTTTCCCCCTTTGGGGCCCCTTTTAAAGGGAAACCCAAAAGGGGGTTTTCAT"
result = count_consecutive_letters(sample_text)

print(result)