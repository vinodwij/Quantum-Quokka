import streamlit as st
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

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

# ---------------- LOGIN PAGE ----------------
def login_gate():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return  # User is already authenticated

    st.markdown("## 🔐 Please log in to continue")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.warning("⚠️ Enter both email and password")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Password FROM Employee WHERE Email = %s", (email,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                st.session_state.authenticated = True
                st.rerun()  # Reload the page to unlock content
            else:
                st.error("❌ Invalid email or password")
        except Exception as e:
            st.error(f"❌ Login failed: {e}")

# Call this at the top of each page to lock access
login_gate()

# Show the rest of the page only after login
if not st.session_state.authenticated:
    st.stop()
