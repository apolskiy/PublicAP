"""Aleksandr Polskiy practice of file manipulation
taking .csv file as an input line by line then printing it
reading the file into dataframe printing it
saving it as .xlsx and .json
opening them reading them into dataframe and printing those dataframes"""

import os
import sys
import pandas as pd
from tabulate import tabulate
file_path = 'flowers.csv'
data = []

if os.path.exists(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            # .strip() removes leading/trailing whitespace including newlines
            data.append(line.strip())
    file.close()
else:
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)
print("Printing Data from CSV file as array")
print(data)



file_path = 'flowers.csv'
df = pd.read_csv(file_path)
print("\nPrinting unformatted extracted Data Frame from csv file:")
print(df.head())

#writing dataframe contents into excel and json formatted files
df.to_excel('flowers.xlsx', index=False)
df.to_json('flowers.json', index=False)


#import previously created excel file into another dataframe and print the dataframe
file_path = 'flowers.xlsx'
df1 = pd.read_excel(file_path)
print("\nPrinting Unformatted Data Frame from Excel:")
print(df1.head())

print("\nPrinting Tabulated Data Frame from Excel:")
print(tabulate(df1, showindex=False, headers=df1.columns, numalign="left"))

#open previously created json file, extract data into a dataframe and print the dataframe
file_path = 'flowers.json'
df2 = pd.read_json(file_path)
print("\nPrinting tabulated with header separation DataFrame from JSON:")
#print(df2.head())
print(tabulate(df2, showindex=False, headers=df2.columns, numalign="left",tablefmt="pretty"))
