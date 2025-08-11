import streamlit as st
import mysql.connector
import bcrypt
import os

# Load DB credentials from secrets.toml
DB_HOST = st.secrets["db"]["host"]
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASS = st.secrets["db"]["pass"]
DB_PORT = int(st.secrets["db"]["port"])  # Ensure it's an integer

def get_connection():
    try:
        # If using Railway's public URL (gondola.proxy...), enable SSL
        ssl_required = "proxy.rlwy.net" in DB_HOST

        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            ssl_disabled=not ssl_required
        )
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

def login_gate():
    # Initialize session state variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'email' not in st.session_state:
        st.session_state.email = None
    if 'name' not in st.session_state:
        st.session_state.name = None

    # If user is authenticated, return to allow page rendering
    if st.session_state.authenticated:
        return

    # Display login form
    st.markdown("## 🔐 Login to Access the Application")
    email = st.text_input("Email", key="login_email_unique")
    password = st.text_input("Password", type="password", key="login_password_unique")

    if st.button("Login"):
        if not email or not password:
            st.warning("⚠️ Please enter both email and password")
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            # Fetch Name, Password, IsAdmin
            cursor.execute("SELECT Name, Password, IsAdmin FROM Employee WHERE Email = %s", (email,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                name, stored_password, is_admin = result
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    st.session_state.authenticated = True
                    st.session_state.is_admin = bool(is_admin)
                    st.session_state.email = email
                    st.session_state.name = name if name else email  # Fallback to email if Name is NULL
                    st.success(f"✅ Login successful for {st.session_state.name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            else:
                st.error("❌ Email not found")
        except mysql.connector.Error as e:
            st.error(f"❌ Login failed: {e}")
            return

    # Stop rendering until authenticated
    st.stop()

def check_permission(page_name):
    # Pages accessible to non-admin users
    allowed_pages = ["5_Milestone_and_Status_Updates", "7_Risks_and_Issues"]
    if not st.session_state.is_admin and page_name not in allowed_pages:
        st.error("❌ You do not have permission to access this page.")
        st.stop()

def logout():
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.email = None
    st.session_state.name = None
    st.rerun()
