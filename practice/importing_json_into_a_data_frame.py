#Aleksandr Polskiy script to import JSON data from a file into a pandas DataFrame.
import argparse
import sys
import json
import pandas as pd

def import_json_to_df(f_path):
    """import_json_to_df function imports JSON data from a file into a pandas DataFrame."""
    try:
        with (open(f_path, 'r', encoding='utf-8') as file):
            data = json.load(file)
            employees_data = data['employees']
            company_info = data['company_info']
            departments_data = data['departments']



            #employees_df = pd.json_normalize(employees_data)
            employees_df = pd.json_normalize(
                data['employees'],
                meta=['id', 'firstName', 'lastName', 'position', 'skills'],
                record_path=['projects'],
                record_prefix='project_'
            )

            # Merge skills back into the main DataFrame (json_normalize flattens records separately)
            # We need to drop duplicates from the original normalized data which only contains
            # the non-project specific info
            employees_base_df = pd.json_normalize(data['employees'])
            # Drop the columns that json_normalize already extracted
            # as we don't want it nested in final output
            employees_base_df = employees_base_df.drop(columns=['projects',
                                                                'skills','firstName','lastName','position'])

            # Merge the base info back into the projects DF, keeping a row for each project
            employees_df = pd.merge(employees_df, employees_base_df, on='id', how='left')
            print(employees_df.columns)

            employees_df['fullName'] = employees_df['firstName'] + ' ' + employees_df['lastName']

            departments_df = pd.DataFrame(list(departments_data.items()),
                                          columns=['department', 'employeeNamesList'])
            departments_df = departments_df.explode('employeeNamesList')
            departments_df.rename(columns={'employeeNamesList': 'fullName'}, inplace=True)


            # --- Step 3: Merge Employees and Departments ---
            merged_df = pd.merge(employees_df, departments_df[['department', 'fullName']],
                                 on='fullName', how='left')
            print(merged_df['department'])


            merged_df.drop(columns=['fullName'], inplace=True)  # drop temp full_name columns
            merged_df['companyName'] = company_info['companyName']
            for key, value in company_info['location'].items():
                merged_df[f'{key}'] = value
            merged_df.set_index(['firstName', 'lastName'],inplace=True)

            #print(merged_df.columns)
            return merged_df
    except FileNotFoundError:
        print(f"Error: File '{f_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file '{f_path}'.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parses contents of a json '
                                                 'file into a dataframe.')
    parser.add_argument('-f','--src',type=str, default="json_to_parse.json",
                        help='source json file')
    args = parser.parse_args()
    file_path= args.src

    data = import_json_to_df(file_path)
    pd.set_option('display.max_columns', None)
    print(data.loc['Alice','Smith'])
    print(data.loc['Bob','Johnson'])
    #print(data.loc['Charlie','Brown'])
    print(data)
    #print(data['firstName'])
    #print(data['lastName'])