import os
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import requests
from flask import Flask, jsonify, request
import threading  # 🚀 Background task chalane ke liye

app = Flask(__name__)

# SerpApi Key
SERPAPI_KEY = "969eab93ccbfc8b3c9603c4206ca888acd157625cf6fd71dd7e938d17ff14748"

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
        print(f"Error downloading image: {e}")
    return None

def crawl_image_on_internet(image_url):
    if not SERPAPI_KEY or "YOUR_SERPAPI" in SERPAPI_KEY:
        print("⚠️ SerpApi Key not configured. Skipping internet crawl.")
        return []

    print(f"🔍 Crawling image on internet via SerpApi...")
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": SERPAPI_KEY
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            results = response.json()
            leaked_links = []
            visual_matches = results.get("visual_matches", [])
            for match in visual_matches:
                link = match.get("link")
                title = match.get("title", "Unknown Source")
                if link and link not in leaked_links:
                    leaked_links.append(f"{title}: {link}")
            return leaked_links[:5]
    except Exception as e:
        print(f"🔴 Error during crawling: {e}")
    return []

# 🚀 Ye function background mein aaram se kaam karega bina Elementor ko rok ke
def process_kyc_async(user_name, selfie_url, id_url):
    print(f"⚡ Background processing started for {user_name}...")
    faces_count = 0
    kyc_status = "Pending"

    # 1. Face Detection
    if selfie_url:
        try:
            img = download_image(selfie_url)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                if hasattr(cv2, 'CascadeClassifier'):
                    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30,30))
                    faces_count = len(faces)
                    kyc_status = "Face Detected" if faces_count > 0 else "No Face Detected"
                else:
                    faces_count = 1
                    kyc_status = "Processed"
            else:
                kyc_status = "Download Failed"
        except Exception as e:
            kyc_status = "Error"

    # 2. Internet Crawling (Reverse Image Search)
    found_leaks = []
    if selfie_url:
        found_leaks = crawl_image_on_internet(selfie_url)

    leaks_str = ", ".join(found_leaks) if found_leaks else "No Leaks Found"

    # 3. Database Insertion
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            query = """
                INSERT INTO user_kyc (username, selfie_url, id_url, status, faces_detected, leaked_urls) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_name, selfie_url, id_url, kyc_status, faces_count, leaks_str))
            db.commit()
            print(f"🟢 Saved {user_name}'s data to DB with {len(found_leaks)} leaks.")
            cursor.close()
            db.close()
        except Exception as db_err:
            print(f"🔴 DB Insert Error: {db_err}")
    else:
        print("🔴 DB Connection unavailable.")

@app.route('/')
def home():
    return jsonify({"status": "Online"})

@app.route('/kyc-submit', methods=['POST'])
def kyc_submit():
    # Parse data instantly
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    detected_urls = []
    user_name = "Unknown User"

    for key, value in data.items():
        if 'name' in key.lower():
            user_name = value
        if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
            detected_urls.append((key, value))

    selfie_url = None
    id_url = None

    for field_name, url in detected_urls:
        if 'selfie' in field_name.lower():
            selfie_url = url
        elif 'id' in field_name.lower() or 'identity' in field_name.lower():
            id_url = url
    
    if not selfie_url and len(detected_urls) > 0:
        selfie_url = detected_urls[0][1]
    if not id_url and len(detected_urls) > 1:
        id_url = detected_urls[1][1]

    # 🚀 Sabse important: Background process shuru karke turant response bhejdo (0.1 seconds mein)
    threading.Thread(target=process_kyc_async, args=(user_name, selfie_url, id_url)).start()

    # WordPress ko response de do taaki green checkmark aa jaye
    return jsonify({
        "status": "success",
        "message": "Form received successfully!"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
