from flask import Flask, request, render_template, send_from_directory, jsonify, Response
import os
import sqlite3
import cv2
import face_recognition
import time
import webbrowser
from threading import Timer

app = Flask(__name__)

# Configuration for the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads/'
DB_PATH = 'student_data.db'

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to capture image from webcam and save it
def capture_image(id):
    cap = cv2.VideoCapture(0)  # Open the default camera

    if not cap.isOpened():
        print("Could not open webcam.")
        return None

    time.sleep(2)  # Allow the camera to initialize

    # Capture the final frame
    ret, frame = cap.read()
    cap.release()

    if ret:
        # Ensure the frame is in BGR color format, then convert to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Save the image with student ID as filename
        img_name = os.path.join(app.config['UPLOAD_FOLDER'], f"{id}.jpg")
        cv2.imwrite(img_name, frame)  # Save the photo as RGB
        return img_name
    else:
        print("Failed to capture image.")
        return None

# Function to check if the user is already registered based on face comparison
def is_user_registered_by_face(new_face_encoding, tolerance=0.5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT photo_path FROM students")
    result = cursor.fetchall()
    conn.close()

    for row in result:
        known_image = face_recognition.load_image_file(row[0])
        try:
            known_face_encoding = face_recognition.face_encodings(known_image)[0]
            matches = face_recognition.compare_faces([known_face_encoding], new_face_encoding, tolerance=tolerance)
            if True in matches:
                return True
        except IndexError:
            print(f"Face encoding failed for image: {row[0]}")
    return False

# Function to check if the student ID is already in the database
def is_id_already_registered(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None  # Returns True if the student ID is already registered

# Route for the student registration page
@app.route('/')
def index():
    return render_template('register.html')

# Route to handle the registration form submission
@app.route('/register', methods=['POST'])
def register_student():
    id = request.form['id']
    name = request.form['name']
    return render_template('camera_window.html', id=id, name=name)

# Camera feed generator for live streaming
def generate_camera_feed():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to fit screen
        frame = cv2.resize(frame, (640, 480))
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

# Route for live camera feed
@app.route('/camera_feed')
def camera_feed():
    return Response(generate_camera_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to capture photo after showing camera feed
@app.route('/capture_photo')
def capture_photo():
    id = request.args.get('id')

    # Check if the student ID already exists in the database
    if is_id_already_registered(id):
        return jsonify({"success": False, "message": "User with this ID already exists!"})

    photo_path = capture_image(id)  # Capture photo using the webcam
    if photo_path:
        new_image = face_recognition.load_image_file(photo_path)  # Load the captured image
        new_face_encoding = face_recognition.face_encodings(new_image)  # Get the face encoding

        if len(new_face_encoding) > 0:
            new_face_encoding = new_face_encoding[0]
            if is_user_registered_by_face(new_face_encoding, tolerance=0.5):  # Check if the face matches any existing user
                os.remove(photo_path)  # Remove the photo if the user already exists
                return jsonify({"success": False, "message": "User already registered based on face!"})

        # Save student to database if not already registered
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Save photo with student's ID as filename (no timestamp needed)
        img_name = os.path.join(app.config['UPLOAD_FOLDER'], f"{id}.jpg")  # Save with ID as filename
        cv2.imwrite(img_name, new_image)  # Save the photo
        c.execute("INSERT INTO students (id, name, photo_path) VALUES (?, ?, ?)", (id, request.args.get('name'), img_name))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Photo captured and saved successfully!"})
    else:
        return jsonify({"success": False, "message": "Failed to capture image."})

# Route to serve images from the uploads directory
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5001/")

# Run the Flask application
if __name__ == '__main__':
    # Create the database and table if not exist
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id TEXT PRIMARY KEY, 
                  name TEXT NOT NULL, 
                  photo_path TEXT NOT NULL)''')
    conn.commit()
    conn.close()

    Timer(1, open_browser).start()
    app.run(port=5001)
