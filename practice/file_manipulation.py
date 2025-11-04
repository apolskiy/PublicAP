#Aleksandr Polskiy practice of file manipulation
#taking .csv file as an imput line by line then printing it
#reading the file into dataframe printing it
#saving it as .xlsx and .json
#opening them reading them into dataframe and printing those dataframes

import os
import sys
import pandas as pd
import csv
file_path = 'flowers.csv'
data = []

if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            data.append(line.strip()) # .strip() removes leading/trailing whitespace including newlines
else:
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)
print(data)


file_path = 'flowers.csv'
data = []
with open(file_path, 'r', newline='') as file:
    reader = csv.reader(file)
    for row in reader:
        data.append(row)
file.close()
print(data)



file_path = 'flowers.csv'
df = pd.read_csv(file_path)
print("Printing Data Frame")
print(df.head())


df.to_excel('flowers.xlsx', index=False)
df.to_json('flowers.json', index=False)



file_path = 'flowers.xlsx'
df1 = pd.read_excel(file_path)
print("Printing Data Frame from Excel")
print(df1.head())


file_path = 'flowers.json'
df2 = pd.read_json(file_path)
print("Printing Data Frame from JSON")
print(df2.head())

