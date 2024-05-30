import mysql.connector
import csv
import os
import sys

def usage():
    print("Usage: python %s <user> <password> <database name>" % (sys.argv[0]))
    print("\t<user>: Can be root or another user set up in your SQL database")
    print("\t<password>: Account password used to get into MySQL")
    print("\t<database name>: Name of the database being accessed")
    print("\tIe: python %s root myPassword1 CEM_EVENTS" % (sys.argv[0]))
    print("\tNote: This script assumes you will be using localhost")

# Connect to the database using values passed from the command line. If the connection fails, print the error and exit
def connect_to_database(user, password, database):
    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user=user,
            password=password,
            database=database
        )
    except Exception as e:
        print("Error: Connection to the database has failed")
        print(f"\t{e}")
        exit(1)
    return mydb

# Fetch existing data from the database
def fetch_existing_data():
    try:
        mycursor.execute(f"SELECT * FROM {table_name}")
        return mycursor.fetchall()
    except mysql.connector.Error as err:
        print("Error fetching existing data:", err)
        return []
    
# Prompt the user for the path to the CSV file. Handles errors if users enter wrong file and prompts again
def get_csv_file_path():
    while True:
        file_path = input("Enter the path to the CSV file (make sure to include .csv): ")
        if not file_path.lower().endswith('.csv') or not os.path.isfile(file_path):
            print("Invalid file. Please make sure the file exists and has a .csv extension.\n")
        else:
            return file_path

# exit program if the wrong number of arguments is passed through CLI
if len(sys.argv) != 4:
    usage()
    exit(1)

# Setup the database connection using the command line arguments
mydb = connect_to_database(sys.argv[1], sys.argv[2], sys.argv[3])
mycursor = mydb.cursor()
        
file_path = get_csv_file_path()

# Open the CSV file and read the contents
with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
    csv_reader = csv.reader(csvfile)

    # Skip any initial BOM or non-printable characters
    first_row = next(csv_reader)
    table_name_row = [cell.strip() for cell in first_row if cell.strip()]

    # Use the first non-empty cell as the table name
    table_name = table_name_row[0]
    table_columns = ', '.join(table_name_row[1:])

    existing_data = fetch_existing_data()

    # Identify new entries from the CSV data
    new_entries = []
    for row in csv_reader:
        if tuple(row[1:]) not in existing_data:
            new_entries.append(row)

    # Insert new entries into the database
    for row in new_entries:
        values = tuple(cell.strip() for cell in row[1:])
        sql_statement = f"INSERT INTO `{table_name}` ({table_columns}) VALUES ({', '.join(['%s'] * len(values))})"

        # Print the SQL statement and values being executed
        print("Executing SQL:", sql_statement)
        print("With Values:", values)

        try:
            # Execute the statement
            mycursor.execute(sql_statement, values)
            # Handle MySQL database-related errors
        except mysql.connector.Error as err:
            print("MySQL Error:", err)
            # Handle any other errors
        except Exception as e:
            print("Error executing SQL:", e)

print("\nChanges were successfully committed to the database.\n")
mydb.commit()
