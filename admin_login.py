from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "admin_secret_key"  # Required for session management
DB_PATH = 'student_data.db'

# Route: Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verify admin credentials
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_home'))
        else:
            flash("Invalid Username or Password. Please try again.")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# Route: Admin Home
@app.route('/admin_home')
def admin_home():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_home.html')

# Route: Faculty Registration
@app.route('/register_faculty', methods=['GET', 'POST'])
def register_faculty():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        faculty_id = request.form['id']
        name = request.form['name']
        subject = request.form['subject']
        year = request.form['year']
        semester = request.form['semester']
        password = request.form['password']

        # Add faculty to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO faculty (id, name, subject, year, semester, password) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (faculty_id, name, subject, year, semester, password))
        conn.commit()
        conn.close()
        flash("Faculty registered successfully!")
        return redirect(url_for('register_faculty'))

    return render_template('register_faculty.html')

# Faculty list route
@app.route('/faculty_list')
def faculty_list():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, subject, year, semester FROM faculty")
    faculty_data = cursor.fetchall()
    conn.close()

    return render_template('faculty_list.html', faculty_data=faculty_data)


@app.route('/check_all_attendance')
def check_all_attendance():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # Retrieve all attendance data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, student_name, subject, 
               COUNT(CASE WHEN status = 'Present' THEN 1 END) AS present_count,
               COUNT(*) AS total_classes
        FROM attendance
        GROUP BY student_id, student_name, subject
    """)
    attendance_records = cursor.fetchall()
    conn.close()

    # Process attendance data
    student_summary = {}
    for record in attendance_records:
        student_id, student_name, subject, present_count, total_classes = record
        percentage = (present_count / total_classes) * 100 if total_classes > 0 else 0

        if student_id not in student_summary:
            student_summary[student_id] = {
                'name': student_name,
                'subjects': {},
                'overall_present': 0,
                'overall_total': 0
            }
        student_summary[student_id]['subjects'][subject] = round(percentage, 2)
        student_summary[student_id]['overall_present'] += present_count
        student_summary[student_id]['overall_total'] += total_classes
    # Calculate overall percentages
    for student_id, data in student_summary.items():
        data['overall_percentage'] = round(
            (data['overall_present'] / data['overall_total']) * 100, 2
        ) if data['overall_total'] > 0 else 0

    return render_template('attendance_summary_admin.html', student_summary=student_summary)

# Route: Logout
@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(port=5005)
