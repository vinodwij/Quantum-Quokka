import streamlit as st
import mysql.connector
import os
from datetime import datetime
import pandas as pd
from utils.utils import load_css_once

# Main UI
st.set_page_config(page_title="Risks and Issues", layout="wide")
st.title("🛠️ Risks and Issues Management")

load_css_once()

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

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        return None

def get_employee_id(email):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM Employee WHERE Email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except mysql.connector.Error as e:
        st.error(f"❌ Error fetching employee ID: {str(e)}")
        return None

def fetch_employees():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Name FROM Employee ORDER BY Name")
        employees = cursor.fetchall()
        cursor.close()
        conn.close()
        return employees
    except mysql.connector.Error as e:
        st.error(f"❌ Error fetching employees: {str(e)}")
        return []
    finally:
        if conn.is_connected():
            conn.close()

def fetch_demands():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        if st.session_state.is_admin:
            cursor.execute("SELECT ID, Name FROM Demand ORDER BY Name")
        else:
            cursor.execute("""
                SELECT D.ID, D.Name
                FROM Demand D
                JOIN Employee E ON D.ProjectManagerID = E.ID
                WHERE E.Email = %s
                ORDER BY D.Name
            """, (st.session_state.email,))
        demands = cursor.fetchall()
        cursor.close()
        conn.close()
        return demands
    except mysql.connector.Error as e:
        st.error(f"❌ Error fetching demands: {str(e)}")
        return []
    finally:
        if conn.is_connected():
            conn.close()

def insert_issue(employee_id, demand_id, issue_description, status, resolution_description, resolution_time):
    conn = get_db_connection()
    if not conn:
        return False
    try:
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
        return True
    except mysql.connector.Error as e:
        st.error(f"❌ Error inserting issue: {str(e)}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_issues(order="DESC", only_pending=False):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        cursor = conn.cursor(dictionary=True)
        if st.session_state.is_admin:
            query = f"""
                SELECT I.EmployeeID, I.DemandID, I.TimeRaised,
                       E.Name AS EmployeeName, D.Name AS DemandName,
                       I.IssueDescription, I.Status, I.ResolutionDescription, I.ResolutionTime
                FROM Issues I
                JOIN Employee E ON I.EmployeeID = E.ID
                JOIN Demand D ON I.DemandID = D.ID
                {"WHERE I.Status = 'Pending'" if only_pending else ""}
                ORDER BY I.TimeRaised {order}
            """
            cursor.execute(query)
        else:
            query = f"""
                SELECT I.EmployeeID, I.DemandID, I.TimeRaised,
                       E.Name AS EmployeeName, D.Name AS DemandName,
                       I.IssueDescription, I.Status, I.ResolutionDescription, I.ResolutionTime
                FROM Issues I
                JOIN Employee E ON I.EmployeeID = E.ID
                JOIN Demand D ON I.DemandID = D.ID
                JOIN Employee E2 ON D.ProjectManagerID = E2.ID
                WHERE E2.Email = %s
                {"AND I.Status = 'Pending'" if only_pending else ""}
                ORDER BY I.TimeRaised {order}
            """
            cursor.execute(query, (st.session_state.email,))
        issues = cursor.fetchall()
        return pd.DataFrame(issues)
    except mysql.connector.Error as e:
        st.error(f"❌ Error fetching issues: {str(e)}")
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_issue(employee_id, demand_id, time_raised, new_description, new_status, resolution_description=None, resolution_time=None):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if new_status == "Resolved":
            cursor.execute("""
                UPDATE Issues
                SET IssueDescription=%s, Status=%s, ResolutionDescription=%s, ResolutionTime=%s
                WHERE EmployeeID=%s AND DemandID=%s AND TimeRaised=%s
            """, (new_description, new_status, resolution_description, resolution_time, employee_id, demand_id, time_raised))
        else:
            cursor.execute("""
                UPDATE Issues
                SET IssueDescription=%s, Status=%s, ResolutionDescription=NULL, ResolutionTime=NULL
                WHERE EmployeeID=%s AND DemandID=%s AND TimeRaised=%s
            """, (new_description, new_status, employee_id, demand_id, time_raised))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"❌ Error updating issue: {str(e)}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def insert_risk(employee_id, demand_id, risk_description, status, resolution_description, resolution_time):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        time_raised = datetime.now()
        if status == 'Resolved':
            cursor.execute("""
                INSERT INTO Risk (EmployeeID, DemandID, TimeRaised, RiskDescription, Status, ResolutionDescription, ResolutionTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (employee_id, demand_id, time_raised, risk_description, status, resolution_description, resolution_time))
        else:
            cursor.execute("""
                INSERT INTO Risk (EmployeeID, DemandID, TimeRaised, RiskDescription, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (employee_id, demand_id, time_raised, risk_description, status))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"❌ Error inserting risk: {str(e)}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def fetch_risks(order="DESC", only_pending=False):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        cursor = conn.cursor(dictionary=True)
        if st.session_state.is_admin:
            query = f"""
                SELECT I.EmployeeID, I.DemandID, I.TimeRaised,
                       E.Name AS EmployeeName, D.Name AS DemandName,
                       I.RiskDescription, I.Status, I.ResolutionDescription, I.ResolutionTime
                FROM Risk I
                JOIN Employee E ON I.EmployeeID = E.ID
                JOIN Demand D ON I.DemandID = D.ID
                {"WHERE I.Status = 'Pending'" if only_pending else ""}
                ORDER BY I.TimeRaised {order}
            """
            cursor.execute(query)
        else:
            query = f"""
                SELECT I.EmployeeID, I.DemandID, I.TimeRaised,
                       E.Name AS EmployeeName, D.Name AS DemandName,
                       I.RiskDescription, I.Status, I.ResolutionDescription, I.ResolutionTime
                FROM Risk I
                JOIN Employee E ON I.EmployeeID = E.ID
                JOIN Demand D ON I.DemandID = D.ID
                JOIN Employee E2 ON D.ProjectManagerID = E2.ID
                WHERE E2.Email = %s
                {"AND I.Status = 'Pending'" if only_pending else ""}
                ORDER BY I.TimeRaised {order}
            """
            cursor.execute(query, (st.session_state.email,))
        risks = cursor.fetchall()
        return pd.DataFrame(risks)
    except mysql.connector.Error as e:
        st.error(f"❌ Error fetching risks: {str(e)}")
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_risk(employee_id, demand_id, time_raised, new_description, new_status, resolution_description=None, resolution_time=None):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if new_status == "Resolved":
            cursor.execute("""
                UPDATE Risk
                SET RiskDescription=%s, Status=%s, ResolutionDescription=%s, ResolutionTime=%s
                WHERE EmployeeID=%s AND DemandID=%s AND TimeRaised=%s
            """, (new_description, new_status, resolution_description, resolution_time, employee_id, demand_id, time_raised))
        else:
            cursor.execute("""
                UPDATE Risk
                SET RiskDescription=%s, Status=%s, ResolutionDescription=NULL, ResolutionTime=NULL
                WHERE EmployeeID=%s AND DemandID=%s AND TimeRaised=%s
            """, (new_description, new_status, employee_id, demand_id, time_raised))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"❌ Error updating risk: {str(e)}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Initialize session state for success message
if 'success_message' not in st.session_state:
    st.session_state.success_message = None

# Display and clear success message if present
if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = None

# Fetch demands
demands = fetch_demands()
if not demands:
    st.error("❌ Failed to load demands. Please check your database connection or demand assignments.")
else:
    demand_map = {f"{name} (ID: {did})": did for did, name in demands}

    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Raise or View Issues", "✏️ Update Existing Issue", "🚨 Raise or View Risks", "✏️ Update Existing Risks"])

    with tab1:
        with st.form("issue_form"):
            st.subheader("🚨 Raise a New Issue")
            employee_id = get_employee_id(st.session_state.email)
            if not employee_id:
                st.error("❌ Could not retrieve your employee ID. Please check your account.")
            else:
                selected_demand = st.selectbox("Demand", list(demand_map.keys()), key="issue_demand")
                issue_description = st.text_area("Issue Description")
                status = st.selectbox("Status", ["Pending", "Resolved"])

                resolution_description = resolution_time = None
                if status == "Resolved":
                    resolution_description = st.text_area("Resolution Description")

                submitted = st.form_submit_button("Submit Issue")
                if submitted:
                    if not (selected_demand and issue_description and status):
                        st.warning("🚨 All fields must be filled.")
                    elif status == "Resolved" and not resolution_description:
                        st.warning("🚨 Resolution Description is required when status is Resolved.")
                    else:
                        if status == "Resolved":
                            resolution_time = datetime.now()
                        success = insert_issue(
                            employee_id,
                            demand_map[selected_demand],
                            issue_description,
                            status,
                            resolution_description,
                            resolution_time
                        )
                        if success:
                            st.session_state.success_message = "✅ Issue submitted successfully."
                            st.rerun()

        st.markdown("---")
        st.subheader("📋 All Issues")

        sort_order = st.radio("Sort by Time Raised", ["Newest to Oldest", "Oldest to Newest"], horizontal=True, key="issue_sort")
        order_sql = "DESC" if sort_order == "Newest to Oldest" else "ASC"

        all_issues = fetch_issues(order=order_sql)

        # Filtering
        st.markdown("### 🔍 Filter Issues")
        if st.session_state.is_admin:
            emp_filter = st.selectbox("Filter by Employee", ["All"] + [f"{name} (ID: {eid})" for eid, name in fetch_employees()], key="issue_emp_filter")
            demand_filter = st.selectbox("Filter by Demand", ["All"] + list(demand_map.keys()), key="issue_demand_filter")
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Resolved"], key="issue_status_filter")
        else:
            demand_filter = st.selectbox("Filter by Demand", ["All"] + list(demand_map.keys()), key="issue_demand_filter_nonadmin")
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Resolved"], key="issue_status_filter_nonadmin")

        if not all_issues.empty:
            if st.session_state.is_admin:
                if emp_filter != "All":
                    all_issues = all_issues[all_issues["EmployeeName"] == emp_filter.split(" (ID")[0]]
                if demand_filter != "All":
                    all_issues = all_issues[all_issues["DemandName"] == demand_filter.split(" (ID")[0]]
                if status_filter != "All":
                    all_issues = all_issues[all_issues["Status"] == status_filter]
            else:
                if demand_filter != "All":
                    all_issues = all_issues[all_issues["DemandName"] == demand_filter.split(" (ID")[0]]
                if status_filter != "All":
                    all_issues = all_issues[all_issues["Status"] == status_filter]

        if all_issues.empty:
            st.info("No issues match the selected filters.")
        else:
            st.dataframe(all_issues, use_container_width=True)

    with tab2:
        st.subheader("✏️ Update an Existing Issue")
        issues = fetch_issues(order="DESC", only_pending=True)
        if issues.empty:
            st.info("No pending issues found.")
        else:
            issues["Label"] = issues.apply(
                lambda row: f"{row['TimeRaised']} | {row['EmployeeName']} | {row['DemandName']} | {row['IssueDescription'][:30]}...",
                axis=1
            )
            key_map = {
                row["Label"]: (row["EmployeeID"], row["DemandID"], row["TimeRaised"])
                for _, row in issues.iterrows()
            }

            selected_label = st.selectbox("Select Issue to Edit", ["-- Select --"] + list(key_map.keys()), key="issue_select")
            
            if selected_label != "-- Select --":
                emp_id, dem_id, time_raised = key_map[selected_label]
                selected_issue = issues[(issues["EmployeeID"] == emp_id) &
                                        (issues["DemandID"] == dem_id) &
                                        (issues["TimeRaised"] == time_raised)].iloc[0]

                new_demand = st.selectbox("Demand", list(demand_map.keys()), index=list(demand_map.keys()).index(f"{selected_issue['DemandName']} (ID: {dem_id})"), key="issue_update_demand")
                new_description = st.text_area("Update Issue Description", selected_issue["IssueDescription"], key="issue_update_desc")
                new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=["Pending", "Resolved"].index(selected_issue["Status"]), key="issue_update_status")

                new_resolution_description = selected_issue["ResolutionDescription"] or ""
                new_resolution_time = datetime.now() if new_status == "Resolved" else None

                if new_status == "Resolved":
                    new_resolution_description = st.text_area("Update Resolution Description", new_resolution_description, key="issue_update_res_desc")
                else:
                    new_resolution_description = None

                if st.button("Update Issue"):
                    if not new_description:
                        st.warning("🚨 Issue Description cannot be empty.")
                    elif new_status == "Resolved" and not new_resolution_description:
                        st.warning("🚨 Resolution Description is required when status is Resolved.")
                    else:
                        success = update_issue(
                            emp_id, demand_map[new_demand], time_raised,
                            new_description, new_status,
                            new_resolution_description, new_resolution_time
                        )
                        if success:
                            st.session_state.success_message = "✅ Issue updated successfully."
                            st.rerun()

    with tab3:
        with st.form("risk_form"):
            st.subheader("🚨 Raise a New Risk")
            employee_id = get_employee_id(st.session_state.email)
            if not employee_id:
                st.error("❌ Could not retrieve your employee ID. Please check your account.")
            else:
                selected_demand = st.selectbox("Demand", list(demand_map.keys()), key="risk_demand")
                risk_description = st.text_area("Risk Description")
                status = st.selectbox("Status", ["Pending", "Resolved"], key="risk_status")

                resolution_description = resolution_time = None
                if status == "Resolved":
                    resolution_description = st.text_area("Resolution Description", key="risk_res_desc")

                submitted = st.form_submit_button("Submit Risk")
                if submitted:
                    if not (selected_demand and risk_description and status):
                        st.warning("🚨 All fields must be filled.")
                    elif status == "Resolved" and not resolution_description:
                        st.warning("🚨 Resolution Description is required when status is Resolved.")
                    else:
                        if status == "Resolved":
                            resolution_time = datetime.now()
                        success = insert_risk(
                            employee_id,
                            demand_map[selected_demand],
                            risk_description,
                            status,
                            resolution_description,
                            resolution_time
                        )
                        if success:
                            st.session_state.success_message = "✅ Risk submitted successfully."
                            st.rerun()

        st.markdown("---")
        st.subheader("📋 All Risks")

        sort_order = st.radio("Sort by Time Raised", ["Newest to Oldest", "Oldest to Newest"], horizontal=True, key="risk_sort")
        order_sql = "DESC" if sort_order == "Newest to Oldest" else "ASC"

        all_risks = fetch_risks(order=order_sql)

        # Filtering
        st.markdown("### 🔍 Filter Risks")
        if st.session_state.is_admin:
            emp_filter = st.selectbox("Filter by Employee", ["All"] + [f"{name} (ID: {eid})" for eid, name in fetch_employees()], key="risk_emp_filter")
            demand_filter = st.selectbox("Filter by Demand", ["All"] + list(demand_map.keys()), key="risk_demand_filter")
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Resolved"], key="risk_status_filter")
        else:
            demand_filter = st.selectbox("Filter by Demand", ["All"] + list(demand_map.keys()), key="risk_demand_filter_nonadmin")
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Resolved"], key="risk_status_filter_nonadmin")

        if not all_risks.empty:
            if st.session_state.is_admin:
                if emp_filter != "All":
                    all_risks = all_risks[all_risks["EmployeeName"] == emp_filter.split(" (ID")[0]]
                if demand_filter != "All":
                    all_risks = all_risks[all_risks["DemandName"] == demand_filter.split(" (ID")[0]]
                if status_filter != "All":
                    all_risks = all_risks[all_risks["Status"] == status_filter]
            else:
                if demand_filter != "All":
                    all_risks = all_risks[all_risks["DemandName"] == demand_filter.split(" (ID")[0]]
                if status_filter != "All":
                    all_risks = all_risks[all_risks["Status"] == status_filter]

        if all_risks.empty:
            st.info("No risks match the selected filters.")
        else:
            st.dataframe(all_risks, use_container_width=True)

    with tab4:
        st.subheader("✏️ Update an Existing Risk")
        risks = fetch_risks(order="DESC", only_pending=True)
        if risks.empty:
            st.info("No pending risks found.")
        else:
            risks["Label"] = risks.apply(
                lambda row: f"{row['TimeRaised']} | {row['EmployeeName']} | {row['DemandName']} | {row['RiskDescription'][:30]}...",
                axis=1
            )
            key_map = {
                row["Label"]: (row["EmployeeID"], row["DemandID"], row["TimeRaised"])
                for _, row in risks.iterrows()
            }

            selected_label = st.selectbox("Select Risk to Edit", ["-- Select --"] + list(key_map.keys()), key="risk_select")
            
            if selected_label != "-- Select --":
                emp_id, dem_id, time_raised = key_map[selected_label]
                selected_risk = risks[(risks["EmployeeID"] == emp_id) &
                                      (risks["DemandID"] == dem_id) &
                                      (risks["TimeRaised"] == time_raised)].iloc[0]

                new_demand = st.selectbox("Demand", list(demand_map.keys()), index=list(demand_map.keys()).index(f"{selected_risk['DemandName']} (ID: {dem_id})"), key="risk_update_demand")
                new_description = st.text_area("Update Risk Description", selected_risk["RiskDescription"], key="risk_update_desc")
                new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=["Pending", "Resolved"].index(selected_risk["Status"]), key="risk_update_status")

                new_resolution_description = selected_risk["ResolutionDescription"] or ""
                new_resolution_time = datetime.now() if new_status == "Resolved" else None

                if new_status == "Resolved":
                    new_resolution_description = st.text_area("Update Resolution Description", new_resolution_description, key="risk_update_res_desc")
                else:
                    new_resolution_description = None

                if st.button("Update Risk"):
                    if not new_description:
                        st.warning("🚨 Risk Description cannot be empty.")
                    elif new_status == "Resolved" and not new_resolution_description:
                        st.warning("🚨 Resolution Description is required when status is Resolved.")
                    else:
                        success = update_risk(
                            emp_id, demand_map[new_demand], time_raised,
                            new_description, new_status,
                            new_resolution_description, new_resolution_time
                        )
                        if success:
                            st.session_state.success_message = "✅ Risk updated successfully."
                            st.rerun()