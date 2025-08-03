import sqlite3

# Connect to the SQLite database
db_connection = sqlite3.connect('billing.db')
cursor = db_connection.cursor()

# List of tables to delete
tables_to_delete = ['sample', 'sample_table', 'ABC']

for table in tables_to_delete:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Deleted table: {table}")
    except sqlite3.Error as e:
        print(f"Error deleting table {table}: {e}")

# Commit changes and close the connection
db_connection.commit()
db_connection.close()