import bcrypt
import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# ---------------- LOGIN SYSTEM ----------------
st.title("🔐 Employee Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if not email or not password:
        st.warning("⚠️ Both fields are required.")
    else:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check if email exists in the database
            cursor.execute("SELECT Password FROM Employee WHERE Email = %s", (email,))
            result = cursor.fetchone()

            if result:
                # Compare entered password with the stored hash
                stored_hash = result[0]
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    st.success("✅ Login successful.")
                else:
                    st.error("❌ Incorrect password.")
            else:
                st.error("❌ Email not found.") 
            
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"❌ Error: {e}")
