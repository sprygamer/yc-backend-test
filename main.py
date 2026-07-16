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

# 🚀 Robust Webhook Endpoint (Supports Form-Data & JSON)
@app.route('/kyc-submit', methods=['POST'])
def kyc_submit():
    # 1. Sabse pehle WordPress ko 200 OK response bhejte hain taaki frontend par error na aaye
    # Aur processing hum background mein ya iske turant baad karenge.
    
    # Check karein data kis format mein aa raha hai
    if request.is_json:
        data = request.get_json()
    else:
        # Form-data ya URL encoded ko dictionary mein convert karein
        data = request.form.to_dict()
        if not data and request.files:
            # Agar file objects direct aa rahe hain toh unke names check karein
            data = {key: val for key, val in request.form.items()}

    print("--- NEW SUBMISSION RECEIVED ---")
    print("Received Data Keys:", list(data.keys()))
    print("Full Received Data:", data)

    # Elementor fields ke name (case-insensitive search)
    user_name = next((v for k, v in data.items() if 'name' in k.lower()), "Unknown User")
    selfie_url = next((v for k, v in data.items() if 'selfie' in k.lower() or 'upload_your_selfie' in k.lower()), None)
    id_url = next((v for k, v in data.items() if 'id' in k.lower() or 'identity' in k.lower()), None)

    print(f"User: {user_name} | Selfie URL: {selfie_url} | ID URL: {id_url}")

    # Agar koi URL mila hai, toh usko process karenge
    if selfie_url and (selfie_url.startswith('http://') or selfie_url.startswith('https://')):
        selfie_img = download_image(selfie_url)
        if selfie_img is not None:
            gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30,30))
            print(f"ℹ️ Face Detection Run: Found {len(faces)} faces.")
        else:
            print("🔴 Failed to download selfie image.")
    else:
        print("⚠️ No valid Selfie URL found or received in Webhook.")

    # WordPress ko response hamesha success bhejna hai taaki "submission failed" error na aaye
    return jsonify({
        "success": True,
        "status": "received",
        "message": "Webhook processed successfully!"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
