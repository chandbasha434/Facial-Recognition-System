"""import cv2
import os
import time

def capture_image(id):
    cap = cv2.VideoCapture(0)  # Open the default camera

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Could not open webcam.")
        return None  # Return None if the webcam cannot be opened

    # Give the camera some time to initialize
    time.sleep(2)  # Wait for 2 seconds before capturing the frame

    # Capture multiple frames to allow camera to adjust
    for _ in range(5):  # Capture 5 frames before the final capture
        ret, frame = cap.read()

    # Now capture the final frame
    ret, frame = cap.read()  # Capture the final frame

    # Check if frame was captured successfully
    if ret:
        img_name = os.path.join('uploads', f"{id}.jpg")  # Save in 'uploads' folde
        print(f"Saving image to: {img_name}")

        # Save the captured image
        cv2.imwrite(img_name, frame)
        print(f"Image captured and saved as {img_name}")

        cap.release()  # Release the camera
        return img_name  # Return the image path
    else:
        print("Failed to capture image from webcam.")
        cap.release()  # Release the camera if the frame was not captured
        return None

# Example usage
image_path = capture_image("test_image")
if image_path:
    print(f"Image saved at: {image_path}")
else:
    print("Image capture failed.")"""




'''import face_recognition

image = face_recognition.load_image_file("test_image.jpg")
face_locations = face_recognition.face_locations(image)

if len(face_locations) > 0:
    face_encoding = face_recognition.face_encodings(image, face_locations)[0]
    print("Face encoding successful")
else:
    print("No face detected")'''

from flask import Flask
import webbrowser
from threading import Timer

app = Flask(__name__)

# Your Flask routes here

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")  # Replace with your desired URL

if __name__ == "__main__":
    Timer(1, open_browser).start()  # Open the browser after a short delay
    app.run()


