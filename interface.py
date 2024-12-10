from flask import Flask, render_template, redirect, url_for
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('interface.html')

@app.route('/student_login')
def student_login():
    try:
        # Path to student_login.py
        student_login_script_path = os.path.join(os.getcwd(), "student_login.py")
        if not os.path.exists(student_login_script_path):
            return f"Error: student_login.py not found at {student_login_script_path}", 500

        # Start student_login.py as a subprocess
        subprocess.Popen(['python', student_login_script_path], shell=True)

        # Redirect to the student login page
        return redirect("http://127.0.0.1:5003/student_login")
    except Exception as e:
        return f"Error occurred: {str(e)}", 500


@app.route('/admin_login')
def admin_login():
    try:
        # Path to admin_login.py
        admin_login_script_path = os.path.join(os.getcwd(), "admin_login.py")
        if not os.path.exists(admin_login_script_path):
            return f"Error: admin_login.py not found at {admin_login_script_path}", 500

        # Start admin_login.py as a subprocess
        subprocess.Popen(['python', admin_login_script_path], shell=True)

        # Redirect to admin login page running on port 5005
        return redirect("http://127.0.0.1:5005/admin_login")
    except Exception as e:
        return f"Error occurred: {str(e)}", 500


@app.route('/faculty_login')
def faculty_login():
    try:
        # Path to faculty_login.py
        faculty_login_script_path = os.path.join(os.getcwd(), "faculty_login.py")
        if not os.path.exists(faculty_login_script_path):
            return f"Error: faculty_login.py not found at {faculty_login_script_path}", 500

        # Start faculty_login.py as a subprocess
        subprocess.Popen(['python', faculty_login_script_path], shell=True)

        # Redirect to faculty login page running on port 5004
        return redirect("http://127.0.0.1:5004/faculty_login")
    except Exception as e:
        return f"Error occurred: {str(e)}", 500

@app.route('/register_face')
def register_face():
    try:
        # Path to `register.py`
        register_script_path = os.path.join(os.getcwd(), "register.py")
        if not os.path.exists(register_script_path):
            return f"Error: register.py not found at {register_script_path}", 500

        # Start `register.py` as a subprocess
        subprocess.Popen(['python', register_script_path], shell=True)

        # Redirect to `register.py` running on port 5001
        return redirect("http://127.0.0.1:5001/")
    except Exception as e:
        # Capture and return errors
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(port=5002)  # Run this app on port 5002
