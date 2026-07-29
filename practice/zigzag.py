"""Following script takes a string and number of rows as input and zigzags that string
across all the rows vertically forming a new string example:PAYPALISHIRING will be converted to
PAHNAPLSIIGYIR
zigzag:
P     I    N
A   L S  I G
Y A   H R
P     I"""


def convert(s: str, numRows: int) -> str:
    """This function takes an input of a string a number of rows and returns a string, formed
    by creating a zigzag of letters corresponding tho the number of rows vertically"""
    step = 1
    curr = 0
    rows = [""]*numRows
    if len(s) <= 1 or numRows >= len(s) or numRows == 1:
        return s

    for letter in s:
        rows[curr]+= letter
        if curr == 0:
            step = +1
        elif curr == numRows - 1:
            step = -1
        curr += step
    return "".join(rows)

if __name__ == "__main__":
    print(convert("PAYPALISHIRING",3))
    print(convert("AB", 1))