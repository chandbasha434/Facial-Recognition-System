import cv2
import face_recognition
import os
import csv
import sqlite3
import numpy as np
from datetime import datetime, time
from flask import Flask, render_template, redirect, url_for
import time

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'
DB_PATH = 'student_data.db'


# Function to load known faces from the database
def load_known_faces():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, photo_path FROM students")
    results = cursor.fetchall()
    conn.close()

    known_encodings = []
    known_names = []
    student_data = {}
    for student_id, name, photo_path in results:
        if os.path.exists(photo_path):
            image = face_recognition.load_image_file(photo_path)
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) > 0:
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_encodings.append(encoding)
                known_names.append(name)
                student_data[name] = student_id
            else:
                print(f"Warning: No face found in the image for {name}. Skipping.")
        else:
            print(f"Warning: File {photo_path} not found. Skipping.")
    return known_encodings, known_names, student_data


# Function to capture image using the webcam
def capture_image():
    cap = cv2.VideoCapture(0)  # Open the default camera
    # Give the camera some time to initialize
    time.sleep(2)  # Wait for 2 seconds before capturing the frame

    if not cap.isOpened():
        print("Could not open webcam.")
        return None  # Return None if the webcam cannot be opened

    ret, frame = cap.read()  # Capture a single frame
    if ret:
        # Save the captured image temporarily
        img_name = os.path.join(app.config['UPLOAD_FOLDER'], "temp.jpg")
        cv2.imwrite(img_name, frame)
        cap.release()
        return img_name  # Return the image path
    else:
        print("Failed to capture image from webcam.")
        cap.release()  # Release the camera if the frame was not captured
        return None


# Function to get the current date and create a CSV file for it
def get_csv_file_name():
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"{current_date}.csv"


# Function to check if the user has already taken attendance
def has_taken_attendance(name, csv_file):
    if not os.path.exists(csv_file):
        return False  # CSV file does not exist, so no one has taken attendance yet
    with open(csv_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Name'] == name and row['Status'] == 'Present':
                return True  # Name found in CSV as present
    return False


# Function to mark attendance in CSV file
def mark_attendance_in_csv(student_data, present_students):
    csv_file = get_csv_file_name()  # Use the current date as the CSV file name
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    # Write header if CSV does not exist
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Name', 'Date', 'Time', 'Status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    with open(csv_file, 'a', newline='') as csvfile:
        fieldnames = ['ID', 'Name', 'Date', 'Time', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Marking Present Students
        for name in present_students:
            if not has_taken_attendance(name, csv_file):
                writer.writerow({
                    'ID': student_data[name],
                    'Name': name,
                    'Date': date_str,
                    'Time': time_str,
                    'Status': 'Present'
                })


@app.route('/')
def index():
    return render_template('attend.html')


@app.route('/mark_attendance')
def mark_attendance():
    known_encodings, known_names, student_data = load_known_faces()
    image_path = capture_image()

    if not image_path:
        return "Could not capture image. Please try again.", 400

    # Load the captured image and find face locations and encodings
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_face_locations = face_recognition.face_locations(unknown_image)
    unknown_face_encodings = face_recognition.face_encodings(unknown_image, unknown_face_locations)

    if len(unknown_face_encodings) == 0:
        return "No face detected in the captured image! Please try again.", 400

    present_students = set()
    for unknown_encoding in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            name = known_names[best_match_index]
            if has_taken_attendance(name, get_csv_file_name()):
                return f"Attendance for {name} has already been marked."
            present_students.add(name)
            # Mark attendance in CSV for the recognized face
            mark_attendance_in_csv(student_data, present_students)
            return render_template('attendance_marked.html', name=name)
        else:
            return render_template('not_registered.html')

    # Mark attendance in CSV for absent students
    mark_attendance_in_csv(student_data, present_students)

    return redirect(url_for('index'))


# Function to mark absentees after 6 PM
@app.route('/mark_absentees')
def mark_absentees():
    current_time = datetime.now().time()
    if current_time < time(11, 23):  # Before 6 PM
        return "Absentees cannot be marked before 6 PM.", 400

    known_encodings, known_names, student_data = load_known_faces()
    csv_file = get_csv_file_name()

    # Check if CSV file exists
    if not os.path.exists(csv_file):
        return "No attendance records found for today. Cannot mark absentees.", 400

    # Get list of present students from the CSV file
    present_students = set()
    with open(csv_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Status'] == 'Present':
                present_students.add(row['Name'])

    # Find students who have not taken attendance
    absent_students = set(student_data.keys()) - present_students

    # Write absentees to CSV
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    with open(csv_file, 'a', newline='') as csvfile:
        fieldnames = ['ID', 'Name', 'Date', 'Time', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for name in absent_students:
            writer.writerow({
                'ID': student_data[name],
                'Name': name,
                'Date': date_str,
                'Time': time_str,
                'Status': 'Absent'
            })

    return f"Absentees marked for {date_str} after 6 PM."


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])  # Create uploads folder if it doesn't exist
    app.run(debug=True)
