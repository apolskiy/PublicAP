"""This is a web scraping script that opens a google doc reads
out a table uses and x and y coordinates to map the characters then prints out
correct characters consecutively using x and y coordinates on screen"""
import requests
from bs4 import BeautifulSoup


def print_grid_from_doc(url):
    """This function fetched the google doc
    parses the x and y coordinates table and retains
    the character mapping to those coordinates
    then adds all three to the list of tuples
    maps coordinates to a dictionary grid
    and then prints an ansi word using those coordinates+characters"""
    # 1. Fetch and Parse the Google Doc HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 2. Extract Table Data
    # Google Doc tables are standard HTML <table> elements
    table = soup.find('table')
    rows = table.find_all('tr')

    coords = []
    # Skip the header row (index 0)
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) >= 3:
            #format: x, char, y
            x = int(cols[0].text.strip())
            char = cols[1].text.strip()
            y = int(cols[2].text.strip())
            coords.append((x, y, char))

    # 3. Render the Grid
    max_x = max(c[0] for c in coords)
    max_y = max(c[1] for c in coords)

    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for x, y, char in coords:
        grid[y][x] = char

    for row in grid:
        print("".join(row))

if __name__ == "__main__":
    print_grid_from_doc("https://docs.google.com/document/d/e/2PACX-1vSZ9d7OCd4QMsjJi2VFQmPYLebG2sGqI879_bSPugwOo_fgRcZLAFyfajPWU91UDiLg-RxRD41lVYRA/pub")