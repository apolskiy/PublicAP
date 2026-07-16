
"""This script finds the biggest gap in a list, provided, the bigger number
follows the smaller one. If numbers are in decreasing order, gap is 0"""
def find_biggest_gap(prices:list) ->int:
    """this function finds the biggest gap in a list, if smaller number
    precedes the bigger number, big numbers preceding smaller ones, get removed
    from participation"""

    #evaluating input prices list
    if not prices or len(prices) < 1:
        return 0
    #proceeding only if prices list has more than one item.
    max_gap = 0
    minprice = prices[0]
    for num in prices[1:]:
        gap = num - minprice
        if gap > max_gap:
            max_gap = gap
        if num < minprice:
            minprice = num

    return max_gap

if __name__ == "__main__":
    print(find_biggest_gap([7,1,3,4,5,6]))
    print(find_biggest_gap([7,6,5,4,3,2,1]))
    print(find_biggest_gap([7, 5, 6, 1, 3, 2, 11]))