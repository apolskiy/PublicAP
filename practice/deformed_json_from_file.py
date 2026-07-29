"""Parsing JSON from file into dictionary, if successfully parsed dictionary
is returned, and then parsed and printed."""
#Aleksandr Polskiy 10/01/2025
# This script parses JSON from file into dictionary, if successfully
# parsed dictionary and true boolean is returned parsed and
# printed by key value pairs. If parsing operation for JSON fails,
# function returns empty dictionary and false boolean
#Before calling the print function, assert is made if JSON parsing was successful
import json

def parse_json(file_path: str) -> dict:
    """This function attempts to open json file and parse it into a dictionary
    it returns a tuple containing the dictionary and a boolean indicating success"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Json could not be parsed: {file_path}")
        return {}

def print_json(data: list | dict):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"Dictionary: {key}")  # Print the key before descending into nested structure
                print_json(value)
            else:
                print(f"{key}:{value}")
    elif isinstance(data, list):
        for item in data:
            print_json(item)
    else:
        assert False, "Invalid data type"

if __name__ == "__main__":
    #parse_jason function output is returned as a dictionary variable
    dictionary = parse_json("deformed_json_false.json")
    #assertion is made if JSON parsing was successful
    assert dictionary is not None, f"Json could not be parsed: deformed_python.json"
    #print(dictionary)

    if dictionary is not None:
        print_json(dictionary)
