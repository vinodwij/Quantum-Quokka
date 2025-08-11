import streamlit as st
import mysql.connector
import os
from datetime import date
import pandas as pd
from utils.utils import load_css_once


# --- UI Setup ---
st.set_page_config(page_title="DAB Status Updater", layout="centered")
st.title("📋 DAB Status Updater")

load_css_once()

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
DB_PORT = st.secrets["db"]["port"]  # ✅ Added port

def get_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT  # ✅ Ensure correct port is used
        )
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

# --- Fetch Demand List ---
def get_demand_list():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name FROM Demand")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        st.error(f"Error fetching demands: {e}")
        return []

# --- Fetch Previous DAB Entries ---
def get_dab_updates(demand_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Date, Status, Notes
            FROM DAB
            WHERE DemandID = %s
            ORDER BY Date DESC
        """, (demand_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(result, columns=["Date", "Status", "Notes"])
    except Exception as e:
        st.error(f"Error fetching DAB updates: {e}")
        return pd.DataFrame()

# Load demands
demand_list = get_demand_list()
demand_map = {f"{name} (ID: {did})": did for did, name in demand_list}

# Show dropdown with no default selected
selected_demand_label = st.selectbox("Select Demand", ["-- Select Demand --"] + list(demand_map.keys()))
demand_id = demand_map.get(selected_demand_label) if selected_demand_label != "-- Select Demand --" else None

# Store submission state
if "dab_submitted" not in st.session_state:
    st.session_state.dab_submitted = False

# Show DAB functionality if demand is selected
if demand_id:
    st.subheader("📜 Previous DAB Updates")

    # Refresh table if just submitted
    if st.session_state.dab_submitted:
        st.session_state.dab_submitted = False

    dab_table = get_dab_updates(demand_id)
    if dab_table.empty:
        st.info("No previous DAB records found for this demand.")
    else:
        st.dataframe(dab_table, use_container_width=True)

    st.subheader("➕ Add / Update DAB Status")

    dab_date = st.date_input("DAB Date", value=date.today())
    dab_status = st.selectbox("DAB Status", ["-- Select Status --", "Approved", "Rejected"])
    dab_notes = st.text_area("Notes (optional)")

    if st.button("Submit DAB Status"):
        if dab_status == "-- Select Status --":
            st.warning("⚠️ Please select a valid DAB status.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO DAB (DemandID, Date, Status, Notes)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE Status = VALUES(Status), Notes = VALUES(Notes)
                """, (demand_id, dab_date, dab_status, dab_notes))
                conn.commit()
                st.success("✅ DAB status updated successfully.")
                st.session_state.dab_submitted = True
                st.rerun() # Refresh page to reload table
            except Exception as e:
                st.error(f"❌ Database error: {e}")
            finally:
                cursor.close()
                conn.close()
else:
    st.info("Please select a demand to view and submit DAB updates.")
