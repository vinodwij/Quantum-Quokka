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

st.set_page_config(page_title="Vendor Registration", layout="centered")
st.title("📋 Vendor Registration")

service_categories = [
    'Workflow Automation',
    'Application Modernization',
    'IOT Driven Digitalization',
    'AI and Machine Learning',
    'Digital Literacy and Learning',
    'Data Intelligence & Analytics',
    'Agriculture Process Automation'
]

# Input fields
vendor_name = st.text_input("Vendor Name")
description = st.text_area("Vendor Description")
category = st.selectbox("Service Category", service_categories)
name = st.text_input("Contact Person Name")
phone = st.text_input("Contact Person Phone Number")
email = st.text_input("Contact Person Email")

# Helper function to check if vendor exists
def vendor_exists(vendor_name):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Vendor WHERE VendorName = %s", (vendor_name,))
        result = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return result > 0
    except Exception as e:
        st.error(f"Error checking for existing vendor: {e}")
        return True  # Fail safe: prevent duplicate insert if check fails

# Form submission
if st.button("Register Vendor"):
    if not all([vendor_name.strip(), description.strip(), category.strip(), name.strip(), phone.strip(), email.strip()]):
        st.warning("⚠️ Please fill out all fields.")
    elif vendor_exists(vendor_name):
        st.error(f"❌ Vendor with the name '{vendor_name}' already exists.")
    else:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME
            )
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
