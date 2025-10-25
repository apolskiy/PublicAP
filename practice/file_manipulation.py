import os
import pandas as pd
import csv
file_path = 'my_data.txt'
data = []
if os
with open(file_path, 'r') as file:
    for line in file:
        data.append(line.strip()) # .strip() removes leading/trailing whitespace including newlines
print(data)


file_path = 'my_data.csv'
data = []
with open(file_path, 'r', newline='') as file:
    reader = csv.reader(file)
    for row in reader:
        data.append(row)
print(data)



file_path = 'my_data.csv'
df = pd.read_csv(file_path)
print(df.head())

file_path = 'my_data.xlsx'
df = pd.read_excel(file_path)
print(df.head())


file_path = 'my_data.json'
df = pd.read_json(file_path)
print(df.head())

