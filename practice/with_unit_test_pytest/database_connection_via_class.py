"""This script creates and utilizes a connection class to the database
queries were not made part of connection class by design"""
import logging
import sqlite3
import tabulate
import unittest

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class DatabaseConnection(object):
    def __init__(self,db_url):
        """DatabaseConnection constructor"""
        self.db_url = db_url
        self.conn = None
        self.conn_id = None
        self.cursor = None

    def __enter__(self):
        """DatabaseConnection, connection initialization"""
        try:
            self.conn = sqlite3.connect(self.db_url)
            self.conn_id = id(self.conn)
            self.cursor = self.conn.cursor()

            logging.debug(f"Connection open: successful "
                          f"| url {self.db_url} | connection_id: {self.conn_id}")
            return self.conn
        except sqlite3.OperationalError as e:
            logging.error(f"Connection open: failed "
                          f"| Operational: error {e} | url: {self.db_url}")
        except sqlite3.Error as e:
            logging.error(f"Connection open: failed "
                          f"| General error: {e} | url: {self.db_url}")
        except Exception as e:
            logging.error(f"Connection open: failed "
                          f"| Exception: {e} | url: {self.db_url}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """DatabaseConnection, connection close"""
        if self.conn:
            if exc_type is None:
                try:
                    self.conn.commit()  # Commit if no error occurred
                    logging.debug(f"Commit before disconnect: successful "
                                  f"| url: {self.db_url}")
                except Exception as e:
                    logging.error(f"Commit before disconnect: failed "
                                  f"| url: {self.db_url}")
            else:
                try:
                    self.conn.rollback() #rollback if error has occured
                    logging.debug(f"Rollback before disconnect: successful "
                                  f"| url: {self.db_url} | Error {exc_val} ")
                except Exception as e:
                    logging.error(f"Rollback before disconnect: failed |Exception: {e} | url: {self.db_url} | Error {exc_val}")

            try:
                self.conn.close()
                logging.debug(f"Connection close: successful ")
            except Exception as e:
                logging.error(f"Connection close: failed | url: {self.db_url} | Error: {exc_val} | Exception: {e}")

class TestDatabaseConnection(unittest.TestCase):
    """TestDatabaseConnection tests DatabaseConnection class and its functions"""
    def test_create_table_memory(self):
        """Connects to sqlite DB in memory creates two tables, inserts rows and fetches data"""
        with DatabaseConnection(':memory:') as conn:
            cursor = conn.cursor()
                # 2. Create a table
            cursor.execute('''
                CREATE TABLE users (
                    name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    employee_id INTEGER PRIMARY KEY
                )
            ''')

            cursor.execute('''
                CREATE TABLE vacation (
                    employee_id INTEGER PRIMARY KEY,
                    pto_hours_remaining INTEGER NOT NULL
                )
            ''')


            conn.commit()

            # 3. Insert data
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id) VALUES (?, ?, ?, ?)",
                   ('George', 'Test1', 'georget1@xyz.com', 123))
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id) VALUES (?, ?, ?, ?)",
                   ('Jonathan', 'Test2', 'under_test2@xyz.com', 257))
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id) VALUES (?, ?, ?, ?)",
                   ('Anne', 'Test3', 'under_test3@xyz.com', 699))

            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining) VALUES (?, ?)",
                           (123,10))
            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining) VALUES (?, ?)",
                           (257,240))
            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining) VALUES (?, ?)",
                           (699,120))

            conn.commit()


            # 4. Query data
            sql_query = ("SELECT DISTINCT users.employee_id,name,last_name, pto_hours_remaining FROM users JOIN vacation on "
                         "users.employee_id = vacation.employee_id ORDER BY pto_hours_remaining")
            cursor.execute(sql_query)

            results = cursor.fetchall()
            print(f"Users in the database: \n {results}")





if __name__ == "__main__":
    unittest.main()