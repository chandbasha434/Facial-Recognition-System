'''from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import pandas as pd
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
app.secret_key = "secret_key"  # Required for session management
DB_PATH = 'student_data.db'

def initialize_attendance_file(subject):
    """
    Create an Excel file for the subject if it does not already exist.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    excel_file = f"{subject}_{date_str}_attendance.xlsx"

    if os.path.exists(excel_file):
        print(f"Attendance file already exists: {excel_file}")
        return excel_file

    # Query all students to populate the file
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    conn.close()

    # Create the attendance file
    attendance_data = [{
        'ID': student[0],
        'Name': student[1],
        'Subject': subject,
        'Date': date_str,
        'Status': 'Absent'
    } for student in students]

    df = pd.DataFrame(attendance_data)
    df.to_excel(excel_file, index=False)
    print(f"Attendance file created: {excel_file}")
    return excel_file

@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        faculty_id = request.form['id']
        password = request.form['password']

        # Verify faculty credentials
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, subject FROM faculty WHERE id = ? AND password = ?", (faculty_id, password))
        faculty = cursor.fetchone()

        if faculty:
            # Login successful, store faculty info in session
            session['faculty_id'] = faculty_id
            session['faculty_name'] = faculty[0]
            session['subject'] = faculty[1]

            # Store active faculty in the database
            cursor.execute("""
                INSERT OR REPLACE INTO active_faculty (faculty_id, subject)
                VALUES (?, ?)
            """, (faculty_id, faculty[1]))
            conn.commit()

            # Initialize the attendance file
            initialize_attendance_file(session['subject'])

            conn.close()
            return redirect(url_for('faculty_home'))
        else:
            conn.close()
            # Login failed
            flash("Invalid ID or Password. Please try again.")
            return redirect(url_for('faculty_login'))
    return render_template('faculty_login.html')


@app.route('/faculty_home')
def faculty_home():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    return render_template('faculty_home.html',
                           faculty_name=session['faculty_name'],
                           subject=session['subject'])

@app.route('/check_attendance')
def check_attendance():
    """
    Calculate and display the overall attendance percentage of each student
    for the faculty's respective subject.
    """
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))

    subject = session['subject']  # Retrieve the subject for the logged-in faculty
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query attendance data for the subject
    cursor.execute("""
        SELECT student_id, student_name,
               COUNT(CASE WHEN status = 'Present' THEN 1 END) AS present_count,
               COUNT(*) AS total_classes
        FROM attendance
        WHERE subject = ?
        GROUP BY student_id, student_name
    """, (subject,))
    attendance_data = cursor.fetchall()
    conn.close()

    # Calculate percentage
    attendance_summary = [{
        'Student ID': row[0],
        'Name': row[1],
        'Present Count': row[2],
        'Total Classes': row[3],
        'Attendance Percentage': (row[2] / row[3]) * 100 if row[3] > 0 else 0
    } for row in attendance_data]

    return render_template(
        'check_attendance.html',
        attendance_summary=attendance_summary,
        subject=subject  # Pass the subject to the template
    )

@app.route('/mark_attendance')
def mark_attendance():
    try:
        # Path to `attend.py`
        attend_script_path = os.path.join(os.getcwd(), "attend.py")
        if not os.path.exists(attend_script_path):
            return f"Error: attend.py not found at {attend_script_path}", 500

        # Pass subject as an argument to `attend.py`
        subject = session['subject']
        subprocess.Popen(['python', attend_script_path, subject], shell=True)

        # Redirect to `attend.py` running on port 5000
        return redirect("http://127.0.0.1:5000/")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('faculty_login'))

if __name__ == '__main__':
    app.run(port=5004)
'''



from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import pandas as pd
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
app.secret_key = "secret_key"  # Required for session management
DB_PATH = 'student_data.db'

def initialize_attendance_file(subject):
    """
    Create an Excel file for the subject if it does not already exist.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    excel_file = f"{subject}_{date_str}_attendance.xlsx"

    if os.path.exists(excel_file):
        print(f"Attendance file already exists: {excel_file}")
        return excel_file

    # Query all students to populate the file
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    conn.close()

    # Create the attendance file
    attendance_data = [{
        'ID': student[0],
        'Name': student[1],
        'Subject': subject,
        'Date': date_str,
        'Status': 'Absent'
    } for student in students]

    df = pd.DataFrame(attendance_data)
    df.to_excel(excel_file, index=False)
    print(f"Attendance file created: {excel_file}")
    return excel_file

@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        faculty_id = request.form['id']
        password = request.form['password']

        # Verify faculty credentials
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, subject FROM faculty WHERE id = ? AND password = ?", (faculty_id, password))
        faculty = cursor.fetchone()

        if faculty:
            # Login successful, store faculty info in session
            session['faculty_id'] = faculty_id
            session['faculty_name'] = faculty[0]
            session['subject'] = faculty[1]

            # Store active faculty in the database
            cursor.execute("""
                INSERT OR REPLACE INTO active_faculty (faculty_id, subject)
                VALUES (?, ?)
            """, (faculty_id, faculty[1]))
            conn.commit()

            # Initialize the attendance file
            initialize_attendance_file(session['subject'])

            conn.close()
            return redirect(url_for('faculty_home'))
        else:
            conn.close()
            # Login failed
            flash("Invalid ID or Password. Please try again.")
            return redirect(url_for('faculty_login'))
    return render_template('faculty_login.html')


@app.route('/faculty_home')
def faculty_home():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    return render_template('faculty_home.html',
                           faculty_name=session['faculty_name'],
                           subject=session['subject'])

@app.route('/check_attendance')
def check_attendance():
    """
    Calculate and display the overall attendance percentage of each student
    for the faculty's respective subject.
    """
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))

    subject = session['subject']  # Retrieve the subject for the logged-in faculty
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query attendance data for the subject
    cursor.execute("""
        SELECT student_id, student_name,
               COUNT(CASE WHEN status = 'Present' THEN 1 END) AS present_count,
               COUNT(*) AS total_classes
        FROM attendance
        WHERE subject = ?
        GROUP BY student_id, student_name
    """, (subject,))
    attendance_data = cursor.fetchall()
    conn.close()

    # Calculate percentage
    attendance_summary = [{
        'Student ID': row[0],
        'Name': row[1],
        'Present Count': row[2],
        'Total Classes': row[3],
        'Attendance Percentage': (row[2] / row[3]) * 100 if row[3] > 0 else 0
    } for row in attendance_data]

    return render_template(
        'check_attendance.html',
        attendance_summary=attendance_summary,
        subject=subject  # Pass the subject to the template
    )


@app.route('/mark_attendance')
def mark_attendance():
    try:
        # Path to `attend.py`
        attend_script_path = os.path.join(os.getcwd(), "attend.py")
        if not os.path.exists(attend_script_path):
            return f"Error: attend.py not found at {attend_script_path}", 500

        # Pass subject as an argument to `attend.py`
        subject = session['subject']
        subprocess.Popen(['python', attend_script_path, subject], shell=True)

        # Redirect to `attend.py` running on port 5000
        return redirect("http://127.0.0.1:5000/")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('faculty_login'))

if __name__ == '__main__':
    app.run(port=5004)
