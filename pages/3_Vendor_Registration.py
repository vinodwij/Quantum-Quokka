
import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os

st.set_page_config(page_title="Vendor Management", layout="centered")
st.title("📋 Vendor Management")

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

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

service_categories = [
    'Workflow Automation',
    'Application Modernization',
    'IOT Driven Digitalization',
    'AI and Machine Learning',
    'Digital Literacy and Learning',
    'Data Intelligence & Analytics',
    'Agriculture Process Automation'
]

tab1, tab2 = st.tabs(["Vendor Registration", "Vendor Details Update - Admin"])

# Helper function to get DB connection
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# Helper function to check if vendor exists
def vendor_exists(vendor_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Vendor WHERE VendorName = %s", (vendor_name,))
        result = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return result > 0
    except Exception as e:
        st.error(f"Error checking for existing vendor: {e}")
        return True  # Fail safe: prevent duplicate insert if check fails

# --- Vendor Registration Tab ---
with tab1:
    st.subheader("Register New Vendor")

    # Input fields
    vendor_name = st.text_input("Vendor Name")
    description = st.text_area("Vendor Description")
    category = st.selectbox("Service Category", service_categories)
    name = st.text_input("Contact Person Name")
    phone = st.text_input("Contact Person Phone Number")
    email = st.text_input("Contact Person Email")

    # Form submission
    if st.button("Register Vendor"):
        if not all([vendor_name.strip(), description.strip(), category.strip(), name.strip(), phone.strip(), email.strip()]):
            st.warning("⚠️ Please fill out all fields.")
        elif vendor_exists(vendor_name):
            st.error(f"❌ Vendor with the name '{vendor_name}' already exists.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                query = """
                INSERT INTO Vendor (VendorName, Description, ServiceCategory, ContactPersonName, ContactPersonPhoneNumber, ContactPersonEmail)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (vendor_name, description, category, name, phone, email)
                cursor.execute(query, values)
                conn.commit()
                cursor.close()
                conn.close()

                st.success("✅ Vendor registered successfully!")
            except Exception as e:
                st.error(f"❌ Error inserting vendor: {e}")

# --- Vendor Update Tab ---
with tab2:
    st.subheader("Update Vendor Details")

    # Fetch vendor list
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, VendorName FROM Vendor")
        vendors = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error loading vendors: {e}")
        vendors = []

    if vendors:
        vendor_options = [f"{name} (ID: {vid})" for vid, name in vendors]
        selected_vendor = st.selectbox("Select Vendor", ["Select a vendor"] + vendor_options, index=0)

        if selected_vendor != "Select a vendor":
            selected_id = int(selected_vendor.split("(ID:")[1].split(")")[0])

            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM Vendor WHERE ID = %s", (selected_id,))
                vendor_data = cursor.fetchone()
                cursor.close()
                conn.close()
            except Exception as e:
                st.error(f"Error fetching vendor details: {e}")
                vendor_data = None

            if vendor_data:
                new_name = st.text_input("Vendor Name", value=vendor_data["VendorName"])
                new_description = st.text_area("Vendor Description", value=vendor_data["Description"])
                new_category = st.selectbox("Service Category", service_categories, index=service_categories.index(vendor_data["ServiceCategory"]))
                new_contact_name = st.text_input("Contact Person Name", value=vendor_data["ContactPersonName"])
                new_phone = st.text_input("Contact Person Phone Number", value=vendor_data["ContactPersonPhoneNumber"])
                new_email = st.text_input("Contact Person Email", value=vendor_data["ContactPersonEmail"])

                if st.button("Update Vendor"):
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Vendor SET
                                VendorName = %s,
                                Description = %s,
                                ServiceCategory = %s,
                                ContactPersonName = %s,
                                ContactPersonPhoneNumber = %s,
                                ContactPersonEmail = %s
                            WHERE ID = %s
                        """, (
                            new_name, new_description, new_category,
                            new_contact_name, new_phone, new_email, selected_id
                        ))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("✅ Vendor updated successfully!")
                    except Exception as e:
                        st.error(f"❌ Error updating vendor: {e}")
    else:
        st.info("No vendors found.")
