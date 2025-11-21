"""This script imports JSON data from a file into a dictionary and then printing it."""
#Aleksandr Polskiy
import argparse
import sys
import json

def import_json(f_path):
    """import_json function imports JSON data from a file into a dictionary."""
    try:
        with open(f_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{f_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file '{f_path}'.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parses contents of a json '
                                                 'file into a dictionary.')
    parser.add_argument('-f','--src',type=str, default="json_to_parse.json",
                        help='source json file')
    args = parser.parse_args()
    file_path= args.src

    data = import_json(file_path)
    #print(data)
    for emp in data["employees"]:

        print(f"Employee ID: {emp["id"]},{emp["firstName"]}, {emp["lastName"]}, "
              f"Position: {emp["position"]}")
        for skill in emp["skills"]:
            print(f"\nSkill: {skill}")
        for proj in emp["projects"]:
            print(f"\nProject: {proj["name"]}, Status: {proj["status"]}")
