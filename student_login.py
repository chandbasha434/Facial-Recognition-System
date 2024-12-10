from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"  # Required for flash messages

DB_PATH = 'student_data.db'  # SQLite database file path

# Route for the student login page
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['id']
        student_name = request.form['name']

        # Check credentials in the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ? AND name = ?", (student_id, student_name))
        student = cursor.fetchone()
        conn.close()

        if student:
            # Login successful, redirect to Student Home Page
            return redirect(url_for('student_home', student_id=student_id, student_name=student_name))
        else:
            # Login failed, display an error message
            flash("Invalid ID or Name. Please try again.")
            return redirect(url_for('student_login'))

    return render_template('student_login.html')

# Route for the student home page
@app.route('/student_home/<student_id>/<student_name>')
def student_home(student_id, student_name):
    return render_template('student_home.html', student_id=student_id, student_name=student_name)

# Route for checking attendance
@app.route('/check_attendance/<student_id>')
def check_attendance(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch attendance data for each subject
    cursor.execute("""
        SELECT subject, 
               COUNT(CASE WHEN status = 'Present' THEN 1 END) AS present_count,
               COUNT(*) AS total_classes
        FROM attendance
        WHERE student_id = ?
        GROUP BY subject
    """, (student_id,))
    attendance_data = cursor.fetchall()

    # Prepare data for rendering
    subject_attendance = {}
    total_present = 0
    total_classes = 0

    for subject, present_count, total_classes_in_subject in attendance_data:
        percentage = (present_count / total_classes_in_subject) * 100 if total_classes_in_subject > 0 else 0
        subject_attendance[subject] = {
            'present_count': present_count,
            'total_classes': total_classes_in_subject,
            'percentage': round(percentage, 2)
        }
        total_present += present_count
        total_classes += total_classes_in_subject

    # Calculate overall percentage
    overall_percentage = (total_present / total_classes) * 100 if total_classes > 0 else 0
    conn.close()
    return render_template(
        'attendance.html',
        student_id=student_id,
        subject_attendance=subject_attendance,
        overall_percentage=round(overall_percentage, 2)
    )


if __name__ == '__main__':
    app.run(port=5003)  # Run the Flask app on port 5003
