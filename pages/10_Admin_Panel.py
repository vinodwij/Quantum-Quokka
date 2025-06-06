import streamlit as st
import mysql.connector
import os
import bcrypt
import secrets
from utils.utils import load_css_once

load_css_once()

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("🔐 Admin Panel")

import os
from login import login_gate, check_permission, logout

# Enforce login
login_gate()

# Get current page name
page_name = os.path.basename(__file__).replace(".py", "")

# Check permissions
check_permission(page_name)

# Sidebar content
with st.sidebar:
    name_display = st.session_state.name if st.session_state.name else "Unknown User"
    st.write(f"Logged in as: {name_display}")
    if st.button("Logout"):
        logout()

# Load DB credentials from secrets.toml
DB_HOST = st.secrets["db"]["host"]
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASS = st.secrets["db"]["pass"]


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

tabs = st.tabs(["👤 Employee Registration", "🏢 Company Registration"])

# ---------------- EMPLOYEE REGISTRATION ----------------
import streamlit as st
import mysql.connector
import bcrypt
from login import get_connection
from email_utils import send_registration_email

with tabs[0]:
    st.header("Register New Employee")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT SectorCategory FROM Company;")
        business_sectors = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT Name FROM Company;")
        companies = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"❌ Error fetching sector/company data: {e}")
        business_sectors = []
        companies = []

    # Input fields
    name = st.text_input("Name")
    title = st.text_input("Title")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    status = st.selectbox("Status", ["Active", "Resigned"], index=None)
    business_sector = st.selectbox("Business Sector", business_sectors, index=None)
    company = str(st.selectbox("Company", companies, index=None))

    st.subheader("🔒 Set a Password")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    # Admin flag
    is_admin = st.checkbox("Is Admin")

    # Register button
    if st.button("Register Employee"):
        if not all([name, title, email, phone, status, business_sector, company, password, confirm_password]):
            st.warning("⚠️ All fields must be filled.")
        elif password != confirm_password:
            st.warning("⚠️ Passwords do not match.")
        else:
            try:
                # Hash the password securely
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                conn = get_connection()
                cursor = conn.cursor()

                # Check if email already exists
                cursor.execute("SELECT COUNT(*) FROM Employee WHERE Email = %s", (email,))
                if cursor.fetchone()[0] > 0:
                    st.error("❌ An employee with this email already exists.")
                else:
                    cursor.execute("""
                    INSERT INTO Employee (Name, Title, Email, PhoneNumber, Status, BusinessSector, Company, Password, IsAdmin)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        name, title, email, phone, status, business_sector, company,
                        hashed_password, int(is_admin)
                    ))
                    conn.commit()
                    # Send registration email with email and password
                    send_registration_email(email, password)
                    st.success("✅ Employee registered successfully. A confirmation email has been sent.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cursor.close()
                conn.close()

# ---------------- COMPANY REGISTRATION ----------------
with tabs[1]:
    st.header("Register New Company")

    # Input fields
    company_name = st.text_input("Company Name")
    sector_category = st.selectbox("Sector Category", [
        "Purification/Hand Protection", "Agriculture", "BPO", "Plantations",
        "Investments and Services", "Eco Solutions", "Textile Manufacturing", "Consumer & Retail"
    ], index=None)

    owner_name = st.text_input("Owner Name")  # manual text input for owner name
    description = st.text_area("Description")

    # Registration logic
    if st.button("Register Company"):
        if not (company_name and sector_category and owner_name):
            st.warning("⚠️ Company name, sector, and owner are required.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Check for duplicates using owner name string
                cursor.execute("""
                    SELECT COUNT(*) FROM Company
                    WHERE Name = %s AND OwnerName = %s
                """, (company_name, owner_name))
                if cursor.fetchone()[0] > 0:
                    st.error("❌ A company with the same name and owner already exists.")
                else:
                    cursor.execute("""
                        INSERT INTO Company (Name, SectorCategory, OwnerName, Description)
                        VALUES (%s, %s, %s, %s)
                    """, (company_name, sector_category, owner_name, description))
                    conn.commit()
                    st.success("✅ Company registered successfully.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cursor.close()
                conn.close()
