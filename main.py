import os
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
from flask import Flask, jsonify

app = Flask(__name__)

def test_db_connection():
    try:
        connection = mysql.connector.connect(
            host='193.203.184.232', 
            database='u164985890_HYDPA', 
            user='u164985890_QVr4d',     
            password='8jkSuhve04' 
        )
        if connection.is_connected():
            connection.close()
            return True
    except Error as e:
        print("🔴 DB Connection failed:", e)
        return False
    return False

@app.route('/')
def home():
    db_status = "Connected 🟢" if test_db_connection() else "Failed 🔴"
    return jsonify({
        "status": "Online",
        "database": db_status,
        "message": "YCEA Analytics Backend is running perfectly!"
    })

if __name__ == "__main__":
    # Render automatic PORT environment variable deta hai, hum wahi use karenge
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
