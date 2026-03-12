"""Aleksandr Polskiy
This script creates and utilizes a connection class to the database
queries were not made part of connection class by design"""
# Will add more unittests at a later point
import unittest
import logging
import sqlite3
from tabulate import tabulate


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class DatabaseConnection():
    """DatabaseConnection class allows to create and terminate connections
    to the database"""
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

            logging.debug("Connection open: successful "
                          "| url %s | connection_id: %s",self.db_url,self.conn_id)
            return self.conn
        except sqlite3.OperationalError as e:
            logging.error("Connection open: failed "
                          "| Operational: error %s | url: %s",e,self.db_url)
            return False
        except sqlite3.Error as e:
            logging.error("Connection open: failed "
                          "| General error: %s | url: %s",e,self.db_url)
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """DatabaseConnection, connection close"""
        if self.conn:
            if exc_type is None:
                try:
                    self.conn.commit()  # Commit if no error occurred
                    logging.debug("Commit before disconnect: successful "
                                  "| url: %s",self.db_url)
                except sqlite3.OperationalError as e:
                    logging.error("Commit before disconnect: failed "
                                  "| Exception: %s | url: %s",e,self.db_url)
                except sqlite3.Error as e:
                    logging.error("Commit before disconnect: failed "
                                  "| Exception: %e | url: %s",e,self.db_url)
            else:
                try:
                    self.conn.rollback() #rollback if error has occured
                    logging.debug("Rollback before disconnect: successful "
                                  "| url: %s | Error %s ",self.db_url,exc_val)
                except sqlite3.OperationalError as e:
                    logging.error("Rollback before disconnect: failed "
                                  "| Exception: %s | url: %s",e,self.db_url)
                except sqlite3.Error as e:
                    logging.error("Rollback before disconnect: failed "
                                  "| General error: %s | url: %s",e,self.db_url)

            try:
                self.conn.close()
                logging.debug("Connection close: successful ")
            except sqlite3.OperationalError as e:
                logging.error("Connection close: failed "
                                  "| Exception: %s | url: %s",e,self.db_url)
            except sqlite3.Error as e:
                logging.error("Connection close: failed "
                                  "| Exception: %s | url: %s",e,self.db_url)

class TestDatabaseConnection(unittest.TestCase):
    """TestDatabaseConnection tests DatabaseConnection
    class and its functions"""
    def test_create_table_memory(self):
        """Connects to sqlite DB in memory creates two tables,
        inserts rows and fetches data on PTO, out puts Employee ID,
        first name, last name and PTO hours remaining, sorted by PTO hours
        remaining"""
        expected_result=[(257, 'Jonathan', 'Test2', 240), (699, 'Anne', 'Test3', 120), (123, 'George', 'Test1', 10)]
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
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id)"
                           " VALUES (?, ?, ?, ?)",
                   ('George', 'Test1', 'georget1@xyz.com', 123))
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id)"
                           " VALUES (?, ?, ?, ?)",
                   ('Jonathan', 'Test2', 'under_test2@xyz.com', 257))
            cursor.execute("INSERT INTO users (name, last_name, email, employee_id)"
                           " VALUES (?, ?, ?, ?)",
                   ('Anne', 'Test3', 'under_test3@xyz.com', 699))

            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining)"
                           " VALUES (?, ?)",
                           (123,10))
            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining)"
                           " VALUES (?, ?)",
                           (257,240))
            cursor.execute("INSERT INTO vacation (employee_id, pto_hours_remaining)"
                           " VALUES (?, ?)",
                           (699,120))

            conn.commit()


            # 4. Query data
            #Joining two tables on employee_id, printing employee_id, first name, last name
            #PTO hours remaining, ordering by most PTO hours remaining (need to take vacation)
            sql_query = ("SELECT DISTINCT users.employee_id,name,last_name, "
                         "pto_hours_remaining FROM users JOIN vacation on "
                         "users.employee_id = vacation.employee_id "
                         "ORDER BY pto_hours_remaining DESC")
            cursor.execute(sql_query)
            headers=["Employee ID", "Name", "Last Name", "PTO Hours Remaining"]
            results = cursor.fetchall()
            print(results)
            print(tabulate(results, headers=headers, tablefmt="grid"))
            assert results == expected_result, (f"Results did not match\n "
                                                f"expected result: {expected_result}\n "
                                                f"results: {results}")






if __name__ == "__main__":
    unittest.main()
