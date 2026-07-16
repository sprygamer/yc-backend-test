import os
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Database Connection Function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='193.203.184.232', 
            database='u164985890_HYDPA', 
            user='u164985890_QVr4d',     
            password='8jkSuhve04' 
        )
        return connection
    except Error as e:
        print("🔴 DB Connection failed:", e)
        return None

def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            nparr = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
    return None

@app.route('/')
def home():
    return jsonify({
        "status": "Online",
        "message": "YCEA Safety AI Backend is running!"
    })

# 🚀 Safe Webhook Endpoint
@app.route('/kyc-submit', methods=['POST'])
def kyc_submit():
    # Parse incoming data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    print("\n--- NEW SUBMISSION RECEIVED ---")
    print("Full Raw Data:", data)

    detected_urls = []
    user_name = "Unknown User"

    # Field mapping
    for key, value in data.items():
        if 'name' in key.lower():
            user_name = value
        if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
            detected_urls.append((key, value))

    print(f"Parsed Name: {user_name}")
    print(f"Detected URLs: {detected_urls}")

    # Dono URLs nikalte hain safely
    selfie_url = None
    id_url = None

    for field_name, url in detected_urls:
        if 'selfie' in field_name.lower():
            selfie_url = url
        elif 'id' in field_name.lower() or 'identity' in field_name.lower():
            id_url = url
    
    # Agar specific name match nahi hua toh sequence ke hisab se assign kar dete hain
    if not selfie_url and len(detected_urls) > 0:
        selfie_url = detected_urls[0][1]
    if not id_url and len(detected_urls) > 1:
        id_url = detected_urls[1][1]

    faces_count = 0
    kyc_status = "Pending"

    # Process selfie image for face detection
    if selfie_url:
        try:
            print(f"Processing selfie: {selfie_url}")
            img = download_image(selfie_url)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                if hasattr(cv2, 'CascadeClassifier'):
                    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30,30))
                    faces_count = len(faces)
                    print(f"🟢 OpenCV: Found {faces_count} faces.")
                    if faces_count > 0:
                        kyc_status = "Face Detected"
                    else:
                        kyc_status = "No Face Detected"
                else:
                    faces_count = 1
                    kyc_status = "Processed (No Cascade)"
            else:
                print("🔴 Failed to download selfie image.")
                kyc_status = "Download Failed"
        except Exception as e:
            print(f"⚠️ Image process error: {e}")
            kyc_status = "Error"

    # Save to Database
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            query = """
                INSERT INTO user_kyc (username, selfie_url, id_url, status, faces_detected) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_name, selfie_url, id_url, kyc_status, faces_count))
            db.commit()
            print("🟢 Saved successfully to database!")
            cursor.close()
            db.close()
        except Exception as db_err:
            print(f"🔴 DB Insert Error: {db_err}")
    else:
        print("🔴 DB Connection unavailable, could not save.")

    # Response to Elementor (Always 200 OK)
    return jsonify({
        "status": "success",
        "message": "Data received and logged!",
        "user": user_name,
        "status_logged": kyc_status
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
