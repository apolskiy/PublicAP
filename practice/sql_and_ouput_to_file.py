#Aleksandr Polskiy
"""sqlite database access simulation connector creating tables than querying data"""

import os
import sqlite3

def setup_sqlite_db_query_output_file(output_file,sql_query):
    """setup_sqlite_db_query_output_file function sets up a SQLite database in memory,
    creates a 'users' table, populates it with sample data, executes a SQL query,
    and optionally writes the results to a CSV file."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # 2. Create a table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT
        )
    ''')
    conn.commit()

    # 3. Insert data
    cursor.execute("INSERT INTO users (name, last_name, email) VALUES (?, ?, ?)",
                   ('George', 'Test1', 'georget1@xyz.com'))
    cursor.execute("INSERT INTO users (name, last_name, email) VALUES (?, ?, ?)",
                   ('Jonathan', 'Under_Test2', 'under_test2@xyz.com'))
    conn.commit()


    # 4. Query data
    cursor.execute(sql_query)

    results = cursor.fetchall()
    print("Users in the database:")


    # Determine file mode ('w' for write, 'a' for append)
    file_mode = 'a' if os.path.exists(output_file) else 'w'

    # Write results to file
    if not output_file is None and not output_file == '':
        with open(output_file, file_mode, encoding='utf-8') as f:
            if file_mode == 'w':
                # Write header if creating a new file
                column_names = [i[0] for i in cursor.description]
                f.write(",".join(column_names) + "\n")

            for row in results:
                print(row)
                f.write(",".join(map(str, row)) + "\n")

            print(f"Query results successfully written to {output_file} in '{file_mode}' mode.")
    # 5. Close the connection
    conn.close()




if __name__ == "__main__":
    # Example usage
    SQL_QUERY = "SELECT * FROM users;"
    OUTPUT_FILE = 'output_users.csv'
    setup_sqlite_db_query_output_file(OUTPUT_FILE, SQL_QUERY)
