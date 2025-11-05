#Aleksandr Polskiy inserting data into table using SQL Lite then extracting that data using
#select query into dataframe
#Then doing a selection query from dataframe
import sqlite3
import pandas as pd
from tabulate import tabulate
#initializing sqlite in memory
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

#creating table for users
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER
        )
    ''')
#creating table for products
cursor.execute('''
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            price REAL
        )
    ''')
conn.commit() # Commit the changes to the database

#Inserting data into users and products tables
cursor.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
cursor.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
cursor.execute("INSERT INTO users (name, age) VALUES ('John', 18)")
cursor.execute("INSERT INTO users (name, age) VALUES ('Jonathan', 60)")
cursor.execute("INSERT INTO products (product_name, price) VALUES ('Laptop', 1200.00)")
cursor.execute("INSERT INTO products (product_name, price) VALUES ('Mouse', 25.50)")
cursor.execute("INSERT INTO products (product_name, price) VALUES ('Wifi Headphones', 87.50)")
cursor.execute("INSERT INTO products (product_name, price) VALUES ('External SSD Hard Drive', 242.27)")
conn.commit()

#Select * from users table and inserting it into dataframe df_users
df_users = pd.read_sql_query("SELECT * FROM users", conn)
#Select all products whose price is over 100 and inserting it into dataframe df_products
df_products = pd.read_sql_query("SELECT product_name, price FROM products WHERE price > 100", conn)

#printing both dataframes
print("\nUsers DataFrame:\n")
#print(df_users)
print(tabulate(df_users, showindex=False, headers=df_users.columns, numalign="left"))
print("\nProducts DataFrame:\n")
#print(df_products)
#print(df_products.to_string(justify='left'))
print(tabulate(df_products, showindex=False, headers=df_products.columns, numalign="left",tablefmt="pretty"))
conn.close()