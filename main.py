import os
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

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

# Helper function: URL se image download karke OpenCV format mein convert karne ke liye
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

# 🚀 Elementor Webhook Endpoint
@app.route('/kyc-submit', methods=['POST'])
def kyc_submit():
    # Elementor webhook raw form data ya JSON bhejta hai
    data = request.form.to_dict()
    
    # Debug ke liye console par check karte hain ki kya data aaya
    print("Incoming Form Data:", data)
    
    # Elementor fields ke name check karein (Default form fields Name, Selfie, ID Proof hote hain)
    user_name = data.get('Name') or data.get('name') or "Unknown User"
    selfie_url = data.get('Selfie') or data.get('selfie')
    id_url = data.get('ID_Proof') or data.get('id_proof') or data.get('ID Proof')

    if not selfie_url:
        return jsonify({"success": False, "message": "Selfie is missing!"}), 400

    print(f"Processing KYC for {user_name}...")
    print(f"Selfie URL: {selfie_url}")
    print(f"ID URL: {id_url}")

    # 1. Download Images
    selfie_img = download_image(selfie_url)
    
    if selfie_img is None:
        return jsonify({"success": False, "message": "Failed to download or process Selfie image."}), 400

    # 2. Face Detection Test (Check ki selfie mein koi face hai ya nahi)
    gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
    
    # Simple face detection (Haar Cascade use kar rahe hain jo python cache mein pehle se hota hai)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        return jsonify({
            "success": False, 
            "message": "KYC Rejected: No face detected in the selfie! Please upload a clear photo."
        }), 400

    # Agar face mil gaya, toh abhi ke liye success return kar dete hain
    return jsonify({
        "success": True,
        "message": f"Hello {user_name}, your face was successfully detected! We are processing internet scan.",
        "faces_detected": len(faces)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
