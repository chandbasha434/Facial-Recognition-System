'''import cv2
import face_recognition
import os
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, time
from flask import Flask, render_template, Response
import webbrowser
from threading import Timer

# Flask application setup
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management
app.config['UPLOAD_FOLDER'] = 'uploads/'
DB_PATH = 'student_data.db'  # SQLite database file

# Define attendance time windows
MORNING_START_TIME = time(9, 0)  # Morning: 9:00 AM to 12:00 PM
MORNING_END_TIME = time(12, 0)
AFTERNOON_START_TIME = time(14, 0)  # Afternoon: 2:00 PM to 5:00 PM
AFTERNOON_END_TIME = time(23, 0)

# Global variables for preloaded data
KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA = None, None, None

# Function to fetch the active subject from the database
def get_active_subject():
    """
    Fetch the active subject for the logged-in faculty.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT subject FROM active_faculty LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Function to delete the active subject record
def delete_active_subject():
    """
    Delete the active subject record from the active_faculty table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_faculty LIMIT 1")
    conn.commit()
    conn.close()
    print("Active subject record deleted successfully.")

# Function to load known faces from the database
def preload_known_faces():
    """
    Load and encode student faces from the database and store them in memory
    to speed up face recognition.
    """
    global KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM students")
    results = cursor.fetchall()
    conn.close()

    known_encodings, known_names, student_data = [], [], {}
    for student_id, name, photo_path in results:
        if os.path.exists(photo_path):
            image = face_recognition.load_image_file(photo_path)
            face_locations = face_recognition.face_locations(image, model="hog")  # Faster with 'hog'
            if face_locations:
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_encodings.append(encoding)
                known_names.append(name)
                student_data[name] = student_id
            else:
                print(f"Warning: No face found in the image for {name}. Skipping.")
        else:
            print(f"Warning: File {photo_path} not found. Skipping.")
    KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA = known_encodings, known_names, student_data

# Function to initialize absentees in the database
def initialize_absentees(subject):
    """
    Insert 'Absent' records for all students in the subject for the current date,
    if not already present.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all students for the subject
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    for student_id, student_name in students:
        # Check if attendance already exists for the student
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE student_id = ? AND subject = ? AND date = ?
        """, (student_id, subject, current_date))
        existing_record = cursor.fetchone()

        if not existing_record:
            # Insert 'Absent' record
            cursor.execute("""
                INSERT INTO attendance (student_id, student_name, subject, date, status)
                VALUES (?, ?, ?, ?, 'Absent')
            """, (student_id, student_name, subject, current_date))

    conn.commit()
    conn.close()
    print(f"Initialized absentees for subject {subject} on {current_date}.")

# Function to check if attendance has already been marked
def has_taken_attendance(student_id, subject, date):
    """
    Check if a student has already been marked as 'Present' for a specific subject and date.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status FROM attendance 
        WHERE student_id = ? AND subject = ? AND date = ? AND status = 'Present'
    """, (student_id, subject, date))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# Function to mark attendance
def mark_attendance(present_students, subject):
    """
    Mark the attendance of students who are present and update both the database and the Excel file.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load the Excel file
    excel_file = f"{subject}_{current_date}_attendance.xlsx"
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
    else:
        print(f"Error: Excel file {excel_file} not found.")
        return

    for student_id, name in present_students:
        # Update the database
        if not has_taken_attendance(student_id, subject, current_date):
            cursor.execute("""
                UPDATE attendance
                SET status = 'Present'
                WHERE student_id = ? AND subject = ? AND date = ?
            """, (student_id, subject, current_date))

            # Update the Excel file
            df.loc[df['ID'] == student_id, ['Time', 'Status']] = [datetime.now().strftime("%H:%M:%S"), 'Present']
            print(f"Marked {name} (ID: {student_id}) as Present in Excel and database.")

    conn.commit()
    conn.close()

    # Save updated Excel file
    df.to_excel(excel_file, index=False)
    print(f"Excel file {excel_file} updated successfully.")

# Function to generate the video feed
def generate_camera_feed(subject):
    """
    Start the camera feed and perform face recognition to mark attendance.
    """
    global KNOWN_ENCODINGS, KNOWN_NAMES
    cap = cv2.VideoCapture(0)
    frame_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_counter += 1
        if frame_counter % 2 != 0:  # Skip alternate frames
            continue

        # Process the video frame for face recognition
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")  # Faster detection
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        present_students = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(KNOWN_ENCODINGS, face_encoding, tolerance=0.5)  # Increased tolerance
            face_distances = face_recognition.face_distance(KNOWN_ENCODINGS, face_encoding)
            best_match_index = np.argmin(face_distances)

            if True in matches:
                name = KNOWN_NAMES[best_match_index]
                student_id = STUDENT_DATA[name]
                present_students.append((student_id, name))

                # Draw green rectangle for recognized face
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
            else:
                # Draw red rectangle for unrecognized face
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "Unrecognized", (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

        # Mark attendance for recognized students
        mark_attendance(present_students, subject)

        # Encode and yield the video frame
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('attend.html')

@app.route('/video_feed')
def video_feed():
    subject = get_active_subject()
    if not subject:
        return "No active subject found.", 404
    initialize_absentees(subject)  # Ensure absentees are recorded before marking attendance
    delete_active_subject()  # Delete the subject record after it is fetched
    return Response(generate_camera_feed(subject), mimetype='multipart/x-mixed-replace; boundary=frame')

# Open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    preload_known_faces()
    Timer(1, open_browser).start()
    app.run()



'''





import cv2
import face_recognition
import os
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, time
from flask import Flask, render_template, Response
import webbrowser
from threading import Timer

# Flask application setup
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management
app.config['UPLOAD_FOLDER'] = 'uploads/'
DB_PATH = 'student_data.db'  # SQLite database file

# Define attendance time windows
MORNING_START_TIME = time(9, 0)  # Morning: 9:00 AM to 12:00 PM
MORNING_END_TIME = time(12, 0)
AFTERNOON_START_TIME = time(14, 0)  # Afternoon: 2:00 PM to 5:00 PM
AFTERNOON_END_TIME = time(23, 0)

# Global variables for preloaded data
KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA = None, None, None

# Function to fetch the active subject from the database
def get_active_subject():
    """
    Fetch the active subject for the logged-in faculty.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT subject FROM active_faculty LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Function to delete the active subject record
def delete_active_subject():
    """
    Delete the active subject record from the active_faculty table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_faculty LIMIT 1")
    conn.commit()
    conn.close()
    print("Active subject record deleted successfully.")

# Function to load known faces from the database
def preload_known_faces():
    """
    Load and encode student faces from the database and store them in memory
    to speed up face recognition.
    """
    global KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM students")
    results = cursor.fetchall()
    conn.close()

    known_encodings, known_names, student_data = [], [], {}
    for student_id, name, photo_path in results:
        if os.path.exists(photo_path):
            image = face_recognition.load_image_file(photo_path)
            face_locations = face_recognition.face_locations(image, model="hog")  # Faster with 'hog'
            if face_locations:
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_encodings.append(encoding)
                known_names.append(name)
                student_data[name] = student_id
            else:
                print(f"Warning: No face found in the image for {name}. Skipping.")
        else:
            print(f"Warning: File {photo_path} not found. Skipping.")
    KNOWN_ENCODINGS, KNOWN_NAMES, STUDENT_DATA = known_encodings, known_names, student_data

# Function to initialize absentees in the database
def initialize_absentees(subject):
    """
    Insert 'Absent' records for all students in the subject for the current date,
    if not already present.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all students for the subject
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    for student_id, student_name in students:
        # Check if attendance already exists for the student
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE student_id = ? AND subject = ? AND date = ?
        """, (student_id, subject, current_date))
        existing_record = cursor.fetchone()

        if not existing_record:
            # Insert 'Absent' record
            cursor.execute("""
                INSERT INTO attendance (student_id, student_name, subject, date, status)
                VALUES (?, ?, ?, ?, 'Absent')
            """, (student_id, student_name, subject, current_date))

    conn.commit()
    conn.close()
    print(f"Initialized absentees for subject {subject} on {current_date}.")

# Function to check if attendance has already been marked
def has_taken_attendance(student_id, subject, date):
    """
    Check if a student has already been marked as 'Present' for a specific subject and date.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status FROM attendance 
        WHERE student_id = ? AND subject = ? AND date = ? AND status = 'Present'
    """, (student_id, subject, date))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# Function to mark attendance
def mark_attendance(present_students, subject):
    """
    Mark the attendance of students who are present and update both the database and the Excel file.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load the Excel file
    excel_file = f"{subject}_{current_date}_attendance.xlsx"
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
    else:
        print(f"Error: Excel file {excel_file} not found.")
        return

    for student_id, name in present_students:
        # Update the database
        if not has_taken_attendance(student_id, subject, current_date):
            cursor.execute("""
                UPDATE attendance
                SET status = 'Present'
                WHERE student_id = ? AND subject = ? AND date = ?
            """, (student_id, subject, current_date))

            # Update the Excel file
            df.loc[df['ID'] == student_id, ['Time', 'Status']] = [datetime.now().strftime("%H:%M:%S"), 'Present']
            print(f"Marked {name} (ID: {student_id}) as Present in Excel and database.")

    conn.commit()
    conn.close()

    # Save updated Excel file
    df.to_excel(excel_file, index=False)
    print(f"Excel file {excel_file} updated successfully.")

# Function to generate the video feed
def generate_camera_feed(subject):
    global KNOWN_ENCODINGS, KNOWN_NAMES
    cap = cv2.VideoCapture(0)
    frame_counter = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_counter += 1
        if frame_counter % 2 != 0:  # Skip alternate frames
            continue
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)      # Process the video frame for face recognition
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")  # Faster detection
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        present_students = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(KNOWN_ENCODINGS, face_encoding, tolerance=0.5)  # Increased tolerance
            face_distances = face_recognition.face_distance(KNOWN_ENCODINGS, face_encoding)
            best_match_index = np.argmin(face_distances)
            if True in matches:
                name = KNOWN_NAMES[best_match_index]
                student_id = STUDENT_DATA[name]
                present_students.append((student_id, name))
                # Draw green rectangle for recognized face
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,0,0), 1)
            else:
                # Draw red rectangle for unrecognized face
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "Unrecognized", (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
        mark_attendance(present_students, subject) # Mark attendance for recognized students
        # Encode and yield the video frame
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    cap.release()

@app.route('/')
def index():
    return render_template('attend.html')

@app.route('/video_feed')
def video_feed():
    subject = get_active_subject()
    if not subject:
        return "No active subject found.", 404
    initialize_absentees(subject)  # Ensure absentees are recorded before marking attendance
    delete_active_subject()  # Delete the subject record after it is fetched
    return Response(generate_camera_feed(subject), mimetype='multipart/x-mixed-replace; boundary=frame')

# Open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    preload_known_faces()
    Timer(1, open_browser).start()
    app.run()