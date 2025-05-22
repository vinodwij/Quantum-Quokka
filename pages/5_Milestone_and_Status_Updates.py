import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import date
import pandas as pd

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

st.set_page_config(page_title="Milestone and Status Update", layout="wide")
st.title("📌 Milestone and Status Update")

# --- Fetch available demands ---
def get_demands():
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

def get_employees():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name FROM Employee")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
        return []

# --- Fetch data for display ---
def get_milestones(demand_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Date, Description, AchievedOrNot FROM Milestone WHERE DemandID = %s ORDER BY Date DESC", (demand_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(result, columns=["Date", "Description", "AchievedOrNot"])
    except Exception as e:
        st.error(f"Error fetching milestones: {e}")
        return pd.DataFrame()

def get_status_updates(demand_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT S.Date, S.Description, E.Name AS UpdatedBy 
            FROM Status S
            LEFT JOIN Employee E ON S.UpdatedBy = E.ID
            WHERE S.DemandID = %s ORDER BY S.Date DESC
        """, (demand_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(result, columns=["Date", "Description", "Updated By"])
    except Exception as e:
        st.error(f"Error fetching status updates: {e}")
        return pd.DataFrame()

# --- UI: Demand Selection ---
demands = get_demands()
demand_options = {f"{name} (ID: {id})": id for id, name in demands}

selected_label = st.selectbox("Select Demand", ["-- Select Demand --"] + list(demand_options.keys()))
selected_id = demand_options.get(selected_label) if selected_label != "-- Select Demand --" else None

# --- Show Tables only after selection ---
if selected_id:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚩 Milestones")
        st.dataframe(get_milestones(selected_id), use_container_width=True)

    with col2:
        st.subheader("📈 Status Updates")
        st.dataframe(get_status_updates(selected_id), use_container_width=True)

    # --- Tabs for Additions ---
    tab1, tab2 = st.tabs(["➕ Add Milestone", "➕ Add Status Update"])

    with tab1:
        st.subheader("Add New Milestone")
        milestone_date = st.date_input("Milestone Date", value=date.today(), key="milestone_date")
        milestone_description = st.text_area("Milestone Description", key="milestone_desc")
        achieved_status = st.selectbox("Achieved Status", ["Achieved", "Not Achieved"])

        if st.button("Submit Milestone"):
            if milestone_description.strip() == "":
                st.warning("Please enter a milestone description.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO Milestone (DemandID, Date, Description, AchievedOrNot)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE Description=VALUES(Description), AchievedOrNot=VALUES(AchievedOrNot)
                    """, (selected_id, milestone_date, milestone_description, achieved_status))
                    conn.commit()
                    st.success("✅ Milestone added/updated successfully.")
                except Exception as e:
                    st.error(f"❌ Error adding milestone: {e}")
                finally:
                    cursor.close()
                    conn.close()

    with tab2:
        st.subheader("Add New Status Update")
        status_date = st.date_input("Status Date", value=date.today(), key="status_date")
        status_description = st.text_area("Status Description", key="status_desc")

        employees = get_employees()
        if not employees:
            st.warning("No employees available.")
        else:
            emp_map = {f"{name} (ID: {eid})": eid for eid, name in employees}
            selected_emp_label = st.selectbox("Updated By", ["-- Select Employee --"] + list(emp_map.keys()))
            updated_by_id = emp_map.get(selected_emp_label) if selected_emp_label != "-- Select Employee --" else None

            if st.button("Submit Status Update"):
                if status_description.strip() == "" or not updated_by_id:
                    st.warning("Please complete all fields.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO Status (DemandID, Date, Description, UpdatedBy)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE Description=VALUES(Description), UpdatedBy=VALUES(UpdatedBy)
                        """, (selected_id, status_date, status_description, updated_by_id))
                        conn.commit()
                        st.success("✅ Status update added/updated successfully.")
                    except Exception as e:
                        st.error(f"❌ Error adding status update: {e}")
                    finally:
                        cursor.close()
                        conn.close()
else:
    st.info("Please select a demand to view and update milestones or status.")
