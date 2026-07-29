def print_duplicates_dict(x:list[int]):
    duplicates = {}
    for item in range(len(x)):
        duplicates[x[item]] = duplicates.get(x[item], 0)+1

    for key, value in duplicates.items():
        if value > 1:
            print(f"{key} ")
        #if value == 1:
            #print(f"Number {key} is found {value} time")




if __name__=="__main__":

    print_duplicates_dict(x = [1,2,2,3,3,4,1])

