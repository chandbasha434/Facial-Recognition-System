'''import sqlite3

# Establish a connection to the database
conn = sqlite3.connect('student_data.db')

# Create a cursor object using the connection
cursor = conn.cursor()

# Execute a SQL query using the cursor
cursor.execute("SELECT * FROM faculty")

# Fetch all rows from the executed query
rows = cursor.fetchall()  # This will return all rows as a list of tuples

# Iterate through the rows and print each one
for row in rows:
    print(row)

# Close the cursor and connection when done
cursor.close()
conn.close()
'''

'''import mysql.connector

# Establish a connection
conn = mysql.connector.connect(
    host='localhost',
    user='yourusername',
    password='yourpassword',
    database='yourdatabase'
)

cursor = conn.cursor()

# Query the database
cursor.execute('SELECT * FROM your_table')
for row in cursor.fetchall():
    print(row)

conn.close()'''


'''
import sqlite3

# Path to the SQLite database file
DB_PATH = 'student_data.db'

def create_active_faculty_table():
    """
    Create the active_faculty table in the student_data.db database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # SQL command to create the table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS active_faculty (
        faculty_id TEXT PRIMARY KEY,  -- Unique ID for each faculty member
        subject TEXT NOT NULL         -- Subject assigned to the faculty
    );
    """
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()
    print("active_faculty table created successfully.")

# Call the function to create the table
if __name__ == "__main__":
    create_active_faculty_table()
'''