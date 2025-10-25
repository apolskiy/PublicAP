#!/usr/bin/env python3
#Aleksandr Polskiy
#This script opens syslog.log and extracts on linux using grep on windows using findstr
#all messages associated with an app named ticky
#After the data is extracted all error messages are filtered out and counted and outputted with message text
#and the number of times said text has occurred to error_message.csv
#Also a count of all info and error  messages is made for every user that has logged at least one info or error message
#Those counts are outputted into user_statistics.csv
#though it would have been simpler for this filtration to be done in grep or findstr all the way using subprocess
#I have chosen to do it in a more complex way, in order to highlight utilization of various Python features and capabilities


import sys
import subprocess
import re
import csv
from collections import defaultdict



def run_command(f_command,pattern, filename, custom_command="",custom_pattern=""):
    try:
        # Construct the grep command
        command = [f_command, pattern, filename]
        command2 = [custom_command, custom_pattern]
        if (custom_pattern != None) and (custom_pattern != ""):
            result1 = subprocess.Popen(command, stdout=subprocess.PIPE)
            result2 = subprocess.Popen(command2, stdin=result1.stdout, stdout=subprocess.PIPE)

            result1.stdout.close()
            result= result2.communicate()[0].decode().strip()
            result2.stdout.close()
            print(result)
            return result

        else:
            result = subprocess.run(command, capture_output=True, text=True, check=True)

            return result.stdout

    except subprocess.CalledProcessError as e:

        print(f"Error executing grep: {e}")

        print(f"Stderr: {e.stderr}")

    except FileNotFoundError:

        print(f"Error: {f_command} command or file '{filename}' not found.")


def extract_counts(data, pattern=""):
    search_data = data.splitlines()

    #print("\nSearch DATA:\n")
    #print(search_data)
    #print("\n")
    if pattern.upper() == "ERROR" or pattern.upper()=="INFO":
        return_data = {}#defaultdict(int)
        # Using defaultdict simplifies incrementing
        for line in search_data:
            if re.search(pattern, line):
                print("splitting line"+str(line))
                split_line = line.split(" ")
                item = 6
                error_text = ""
                #print (str(split_line[item]))
                while (item < len(split_line)) and (not split_line[item].startswith('(')):
                    #print("\nWorking on item: ")
                    #print(split_line[item])
                    #print("\n")

                    error_text = error_text+" "+split_line[item]
                    error_text=error_text.strip()
                    print(error_text)
                    print("\n")
                    item+=1
                return_data[error_text] = return_data.get(error_text, 0)+1
                #return_data[error_text] += 1

        return_data = sorted(return_data.items(), key=lambda item: item[1], reverse=True)

    elif pattern.upper()=="USER":
        return_data = {} #defaultdict(lambda: defaultdict(int))
        for line in search_data:
            if re.search("INFO", line):
                user_pattern = r'\(([^)]+)\)$'

                # Search for the pattern in the text
                match = re.search(user_pattern, line)

                # Extract the captured group if a match is found
                if match:
                    username = match.group(1)
                    if not username in return_data:
                        return_data[username] = {"INFO": 0, "ERROR": 0}

                    return_data[username]["INFO"] = return_data[username]["INFO"] + 1
                    #return_data[username]["INFO"]+=1

            elif re.search("ERROR", line):
                user_pattern = r'\(([^)]+)\)$'

                # Search for the pattern in the text
                match = re.search(user_pattern, line)

                if match:
                    username = match.group(1)
                    if not username in return_data:
                        return_data[username] = {"INFO": 0, "ERROR": 0}
                    return_data[username]["ERROR"] = return_data[username]["ERROR"] + 1
                    #return_data[username]["ERROR"]+=1

            else:
                print(f"No match found for ERROR or INFO in line {line}:")
        #sorting by users alphabetically
        return_data=sorted(return_data.items())
        temp_data=[]

        #Sorting INFO Error in reverse alphabetical order for each user
        for item in return_data:
            # Sort the dictionary items by key in reverse alphabetical order
            sorted_dict_items = sorted(item[1].items(), key=lambda x: x[0], reverse=True)
            # Reconstruct the dictionary from the sorted items
            sorted_dict = dict(sorted_dict_items)
            temp_data.append((item[0], sorted_dict))

        return_data=temp_data


        #return_data=dict(sorted(return_data.items()))

    return return_data



def data_to_file(file_path, data,column_names):

    print("\nData to write to file:\n")
    print(data)
    print(type(data))

    with open(file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write the header row
        csv_writer.writerow(column_names)

        # Write the data rows
        for row_tuple in data:
            dict_found = False
            for element in row_tuple:
                if isinstance(element, dict):
                    dict_found=True
                    num_elements = len(element)
            if not dict_found:
                csv_writer.writerow(row_tuple)
            else:
                for item in (element):
                    selected_element =(row_tuple[0],item,element[item])
                    csv_writer.writerow(selected_element)


    csvfile.close()



if __name__ == "__main__":

    first_pattern  =   "ticky:"
    if sys.platform.startswith('linux'):
        print("Operating in Linux Envirnonment")
        command="grep"
    elif sys.platform.startswith('win'):
        print("Operating in Windows Envirnonment")
        command="findstr"
    else:
        print("Operating in Unknown Envirnonment")


    second_command  = command
    second_pattern = "ERROR"
    get_errors = run_command(command, first_pattern, "syslog.log", second_command, second_pattern)


    err_data = extract_counts(get_errors, pattern="ERROR")
    print("\n")
    print("Extracted Error Data:")
    print(err_data)

    data_to_file("error_message.csv", err_data, ["Error", "Count"])



    get_all_messages = run_command(command, first_pattern, "syslog.log")
    user_data = extract_counts(get_all_messages, pattern="USER")



    print("\n")
    print("Extracted User Data:")
    print(type(user_data))
    print(user_data)



    data_to_file("user_statistics.csv", user_data, ["Username", "INFO", "ERROR"])
