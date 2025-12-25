import timeit

def sum_of_numbers(numbers: list[int],value: int) -> int:
    count = 0
    loop1 = 0
    loop2 = 0
    for number in range(len(numbers)-1):
        for number2 in range(number+1,len(numbers)):
            loop1 += 1
            if numbers[number] + numbers[number2] == value:
                loop2 += 1
                print(f"Positions:{number} : {number2}, position values {numbers[number]} : {numbers[number2]}")

                count += 1
    return count, loop1, loop2


if __name__ == "__main__":
    execution_time = timeit.timeit(lambda: sum_of_numbers([0,7,9,4,3,5,6,8,3,3],6), number=10000)
    print(f"Average execution time: {execution_time / 10000:.6f} seconds per run. Result: {sum_of_numbers([0,7,9,4,3,5,6,8,3,3], 6)}")