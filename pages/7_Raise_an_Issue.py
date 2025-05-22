import streamlit as st
import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DB config
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# Fetch employees and demands
def fetch_employees_and_demands():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name FROM Employee ORDER BY Name")
        employees = cursor.fetchall()
        cursor.execute("SELECT ID, Name FROM Demand ORDER BY Name")
        demands = cursor.fetchall()
        cursor.close()
        conn.close()
        return employees, demands
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return [], []

# Insert an issue
def insert_issue(employee_id, demand_id, issue_description, status, resolution_description, resolution_time):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        time_raised = datetime.now()
        if status == 'Resolved':
            cursor.execute("""
                INSERT INTO Issues (EmployeeID, DemandID, TimeRaised, IssueDescription, Status, ResolutionDescription, ResolutionTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (employee_id, demand_id, time_raised, issue_description, status, resolution_description, resolution_time))
        else:
            cursor.execute("""
                INSERT INTO Issues (EmployeeID, DemandID, TimeRaised, IssueDescription, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (employee_id, demand_id, time_raised, issue_description, status))
        conn.commit()
        cursor.close()
        conn.close()
        st.success("✅ Issue successfully raised.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Load employee/demand dropdowns
employees, demands = fetch_employees_and_demands()
employee_map = {f"{name} (ID: {eid})": eid for eid, name in employees}
demand_map = {f"{name} (ID: {did})": did for did, name in demands}

st.set_page_config(page_title="Raise an Issue", layout="centered")
st.title("🚨 Raise an Issue")

with st.form("issue_form"):
    selected_employee = st.selectbox("Employee", list(employee_map.keys()))
    selected_demand = st.selectbox("Demand", list(demand_map.keys()))
    issue_description = st.text_area("Issue Description")
    status = st.selectbox("Status", ["Pending", "Resolved"])

    resolution_description = resolution_time = None
    if status == "Resolved":
        resolution_description = st.text_area("Resolution Description")
        resolution_time = st.date_input("Resolution Date")

    submitted = st.form_submit_button("Submit Issue")
    if submitted:
        if not (selected_employee and selected_demand and issue_description and status):
            st.warning("🚨 All fields must be filled.")
        else:
            insert_issue(
                employee_map[selected_employee],
                demand_map[selected_demand],
                issue_description,
                status,
                resolution_description,
                resolution_time
            )

# Sorting toggle
st.markdown("---")
st.subheader("📋 All Issues")
sort_order = st.radio("Sort by Time Raised", ["Oldest to Newest", "Newest to Oldest"], horizontal=True)

# Fetch and display issues
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    order = "ASC" if sort_order == "Oldest to Newest" else "DESC"
    cursor.execute(f"""
        SELECT I.TimeRaised, E.Name AS EmployeeName, D.Name AS DemandName,
               I.IssueDescription, I.Status, I.ResolutionDescription, I.ResolutionTime
        FROM Issues I
        JOIN Employee E ON I.EmployeeID = E.ID
        JOIN Demand D ON I.DemandID = D.ID
        ORDER BY I.TimeRaised {order}
    """)
    rows = cursor.fetchall()
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No issues have been raised yet.")
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"❌ Could not fetch issues: {e}")
