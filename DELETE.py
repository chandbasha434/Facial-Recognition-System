import sqlite3


def delete_record_by_id(student_id):
    # Establish a connection to the database
    conn = sqlite3.connect('student_data.db')
    cursor = conn.cursor()

    # SQL command to delete a record by student_id
    delete_query = "DELETE FROM students WHERE id = ?"

    # Execute the command and pass the student_id as a parameter
    cursor.execute(delete_query, (student_id,))

    # Commit the transaction to apply the deletion
    conn.commit()
    print(f"Record with id {student_id} deleted successfully.")

    # Close the cursor and connection
    cursor.close()
    conn.close()


# Example usage
delete_record_by_id("R190067")  # Replace '123' with the actual ID you want to delete
