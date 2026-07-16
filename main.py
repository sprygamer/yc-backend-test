import mysql.connector
from mysql.connector import Error
import face_recognition
import sys

print("Python version:", sys.version)
print("🟢 face_recognition library loaded successfully!")

def test_db_connection():
    try:
        connection = mysql.connector.connect(
            host='193.203.184.232', 
            database='u164985890_HYDPA', 
            user='u164985890_QVr4d',     
            password='8jkSuhve04' 
        )
        if connection.is_connected():
            print("🟢 BINGO! Render is successfully connected to Hostinger WordPress Database!")
            connection.close()
    except Error as e:
        print("🔴 Database connection failed. Error:", e)

if __name__ == "__main__":
    test_db_connection()
