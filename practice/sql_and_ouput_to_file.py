import mysql.connector
import os

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database_name'
}

# SQL query
SQL_QUERY = "SELECT * FROM your_table_name;"

# Output file path
OUTPUT_FILE = 'output.txt'

def export_mysql_to_file(db_config, sql_query, output_file):
    """
    Connects to MySQL, executes a SELECT query, and writes/appends results to a file.
    """
    connection = None
    try:
        # Establish connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(sql_query)
        results = cursor.fetchall()

        # Determine file mode ('w' for write, 'a' for append)
        file_mode = 'a' if os.path.exists(output_file) else 'w'

        # Write results to file
        with open(output_file, file_mode) as f:
            if file_mode == 'w':
                # Write header if creating a new file
                column_names = [i[0] for i in cursor.description]
                f.write(",".join(column_names) + "\n")

            for row in results:
                f.write(",".join(map(str, row)) + "\n")

        print(f"Query results successfully written to {output_file} in '{file_mode}' mode.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

# Call the function
export_mysql_to_file(DB_CONFIG, SQL_QUERY, OUTPUT_FILE)