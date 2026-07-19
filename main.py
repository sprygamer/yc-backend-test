import os
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import requests
from flask import Flask, jsonify, request
import threading  # Background task chalane ke liye

app = Flask(__name__)

# 🔑 Apni SerpApi key yahan de
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

# 🌐 Robust Crawling Function
def crawl_image_on_internet(image_url):
    if not SERPAPI_KEY or "YOUR_SERPAPI" in SERPAPI_KEY:
        print("⚠️ SerpApi Key not configured. Skipping internet crawl.")
        return []

    print(f"🔍 Deep crawling image on internet via SerpApi for: {image_url}")
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
            
            print("--- SERPAPI RAW KEYS RECEIVED ---:", list(results.keys()))
            
            # 1. SOURCE 1: Visual Matches
            visual_matches = results.get("visual_matches", [])
            print(f"DEBUG: Found {len(visual_matches)} visual matches in response.")
            for match in visual_matches:
                link = match.get("link")
                title = match.get("title", "Visual Match")
                source = match.get("source", "Google Lens")
                if link and link not in leaked_links:
                    leaked_links.append(f"{source} ({title}): {link}")

            # 2. SOURCE 2: Knowledge Graph
            knowledge_graph = results.get("knowledge_graph", [])
            print(f"DEBUG: Found {len(knowledge_graph)} knowledge graph items.")
            for entity in knowledge_graph:
                link = entity.get("link")
                title = entity.get("title", "Knowledge Source")
                if link and link not in leaked_links:
                    leaked_links.append(f"Official ({title}): {link}")

            # 3. SOURCE 3: Reverse Image Search
            reverse_image_search = results.get("reverse_image_search", {}).get("pages_with_matching_images", [])
            print(f"DEBUG: Found {len(reverse_image_search)} reverse image search pages.")
            for page in reverse_image_search:
                link = page.get("url")
                title = page.get("title", "Web Page Match")
                if link and link not in leaked_links:
                    leaked_links.append(f"Web ({title}): {link}")
            
            print(f"DEBUG: Filtered unique links count: {len(leaked_links)}")
            return leaked_links[:10]
        else:
            print(f"🔴 SerpApi Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"🔴 Error during deep crawling: {e}")
    return []

# 🚀 Async Process (Background processing) WITH EMAIL SUPPORT
def process_kyc_async(user_name, selfie_url, id_url, user_email):
    print(f"⚡ Background processing started for {user_name} ({user_email})...")
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

    # 2. Deep Internet Crawling
    found_leaks = []
    if selfie_url:
        found_leaks = crawl_image_on_internet(selfie_url)

    leaks_str = " | ".join(found_leaks) if found_leaks else "No Leaks Found"

    # 3. Save to MySQL Database (UPDATED QUERY WITH EMAIL)
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            query = """
                INSERT INTO user_kyc (username, selfie_url, id_url, status, faces_detected, leaked_urls, email) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_name, selfie_url, id_url, kyc_status, faces_count, leaks_str, user_email))
            db.commit()
            print(f"🟢 Successfully saved {user_name} to DB with email {user_email} and {len(found_leaks)} leaks!")
            cursor.close()
            db.close()
        except Exception as db_err:
            print(f"🔴 DB Insert Error: {db_err}")
    else:
        print("🔴 DB Connection unavailable.")

@app.route('/')
def home():
    return jsonify({"status": "Online", "message": "Deep crawling with logs and email tracking enabled!"})

@app.route('/kyc-submit', methods=['POST'])
def kyc_submit():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    detected_urls = []
    user_name = "Unknown User"
    user_email = "" # Default empty email

    for key, value in data.items():
        if 'name' in key.lower():
            user_name = value
        # Hidden field se aane wali email ko catch karna
        if 'email' in key.lower():
            user_email = value
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

    # Background thread trigger karein (Passing user_email also)
    threading.Thread(target=process_kyc_async, args=(user_name, selfie_url, id_url, user_email)).start()

    return jsonify({
        "status": "success",
        "message": "Form received and processing started!"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
