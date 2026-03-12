

duplicates={}
x = [1,2,2,3,3,4,1]

for item in range(len(x)):
    duplicates[x[item]] = duplicates.get(x[item], 0)+1

for key, value in duplicates.items():
    if value > 1:
        print(f"Number {key} is found {value} times")
