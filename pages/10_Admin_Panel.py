import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import bcrypt
import secrets

st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("🔐 Admin Panel")

from login import login_gate
login_gate()

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

tabs = st.tabs(["👤 Employee Registration", "🏢 Company Registration"])

# ---------------- EMPLOYEE REGISTRATION ----------------
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
                    st.success("✅ Employee registered successfully.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cursor.close()
                conn.close()


# ---------------- COMPANY REGISTRATION ----------------
with tabs[1]:
    st.header("Register New Company")

    # Load employee data only when this tab is active
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name FROM Employee ORDER BY Name")
        employee_rows = cursor.fetchall()
        employee_options = {f"{name} (ID: {emp_id})": emp_id for emp_id, name in employee_rows}
        cursor.close()
        conn.close()
    except Exception as e:
        st.error("❌ Failed to load employee list")
        employee_options = {}

    # Input fields
    company_name = st.text_input("Company Name")
    sector_category = st.selectbox("Sector Category", [
        "Purification/Hand Protection", "Agriculture", "BPO", "Plantations",
        "Investments and Services", "Eco Solutions", "Textile Manufacturing", "Consumer & Retail"
    ], index=None)
    
    owner_display = st.selectbox("Owner (Employee)", list(employee_options.keys()), index=None) if employee_options else None
    owner_id = employee_options[owner_display] if owner_display else None

    description = st.text_area("Description")

    # Registration logic
    if st.button("Register Company"):
        if not (company_name and sector_category and owner_id):
            st.warning("⚠️ Company name, sector, and owner are required.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Check for duplicates (same company name + owner)
                cursor.execute("""
                    SELECT COUNT(*) FROM Company
                    WHERE Name = %s AND OwnerID = %s
                """, (company_name, owner_id))
                if cursor.fetchone()[0] > 0:
                    st.error("❌ A company with the same name and owner already exists.")
                else:
                    cursor.execute("""
                        INSERT INTO Company (Name, SectorCategory, OwnerID, Description)
                        VALUES (%s, %s, %s, %s)
                    """, (company_name, sector_category, owner_id, description))
                    conn.commit()
                    st.success("✅ Company registered successfully.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cursor.close()
                conn.close()