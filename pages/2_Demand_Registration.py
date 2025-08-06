import streamlit as st
import mysql.connector
import os
from datetime import date
from utils.utils import load_css_once

st.set_page_config(page_title="Demand Management", layout="centered")
st.title("📋 Demand Management")

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

def get_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=st.secrets["db"]["port"]  # ✅ Add this line
        )
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        return None

def get_dropdown_data(query):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as e:
        st.error(f"❌ Dropdown load error: {str(e)}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_id(selection):
    try:
        return int(selection.split("(ID:")[1].split(")")[0])
    except:
        return None

tab1, tab2, tab3 = st.tabs(["Demand Registration", "Demand Update", "Demand Update - Admin"])

with tab1:
    st.header("Register New Demand")

    name = st.text_input("Demand Name", key="reg_name")
    description = st.text_area("Description", key="reg_description")
    received_date = st.date_input("Received Date", value=date.today(), key="reg_received_date")
    status = st.selectbox("Status", ["Active", "Paused", "Abandoned"], key="reg_status")
    phase = st.selectbox("Phase", ["Identify", "Discovery", "Planning", "Delivery", "Live"], key="reg_phase")
    delivery_domain = st.selectbox("Delivery Domain", [
        "Workflow Automation", "Application Modernization", "IOT Driven Digitalization",
        "AI and Machine Learning", "Digital Literacy and Learning",
        "Data Intelligence & Analytics", "Agriculture Process Automation"
    ], key="reg_delivery_domain")
    service_category = st.selectbox("Service Category", ["Implementation", "Advisory"], key="reg_service_category")
    project_sponsor = st.text_input("Project Sponsor", key="reg_project_sponsor")

    company_list = get_dropdown_data("SELECT ID, Name FROM Company")
    employee_list = get_dropdown_data("SELECT ID, Name FROM Employee")
    employee_options = [f"{n} (ID: {i})" for i, n in employee_list]

    company = st.selectbox("Company", [f"{n} (ID: {i})" for i, n in company_list], key="reg_company")
    project_manager = st.selectbox("Project Manager", ["Select a person"] + employee_options, index=0, key="reg_pm")
    owner = st.selectbox("Product Owner", ["Select a person"] + employee_options, index=0, key="reg_owner")
    dto = st.selectbox("Digital Transformation Owner", ["Select a person"] + employee_options, index=0, key="reg_dto")

    company_id = get_id(company)
    pm_id = get_id(project_manager)
    owner_id = get_id(owner)
    dto_id = get_id(dto)

    if st.button("Register Demand", key="reg_submit"):
        if "Select a person" in [project_manager, owner, dto] or len({pm_id, owner_id, dto_id}) < 3:
            st.error("❌ Project Manager, Product Owner, and Digital Transformation Owner must be selected and different.")
        elif not (name and description and received_date and status and phase and delivery_domain and service_category and company_id):
            st.error("❌ Please fill all required fields except Project Sponsor, which is optional.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Demand (
                        Name, Description, ReceivedDate, Status, Phase, DeliveryDomain, ServiceCategory,
                        CompanyID, ProjectManagerID, ProductOwnerID, DTOwnerID, ProjectSponsor
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, description, received_date, status, phase, delivery_domain, service_category,
                    company_id, pm_id, owner_id, dto_id, project_sponsor or None
                ))
                conn.commit()
                st.success(f"✅ Demand '{name}' registered successfully.")
            except mysql.connector.Error as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

with tab2:
    st.header("Update Demand Details")

    demand_list = get_dropdown_data("SELECT ID, Name FROM Demand")
    demand_options = ["Select a demand"] + [f"{n} (ID: {i})" for i, n in demand_list]
    selected_demand = st.selectbox("Select Demand to Update", demand_options, index=0, key="update_demand")

    if selected_demand != "Select a demand":
        demand_id = get_id(selected_demand)
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Demand WHERE ID = %s", (demand_id,))
            demand = cursor.fetchone()
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            st.error(f"❌ Error fetching demand: {str(e)}")
            demand = None

        if demand:
            go_live_date = st.date_input("Go Live Date (optional)", value=demand['GoLiveDate'] if demand['GoLiveDate'] else None, key="update_go_live")
            abandonment_reason = st.text_area("Abandonment Reason", value=demand['AbandonmentReason'] or "", key="update_abandonment")
            priority = st.selectbox("Company Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['CompanyPriority']) if demand['CompanyPriority'] else 0, key="update_priority")
            value_description = st.text_area("Company Value Description", value=demand['CompanyValueDescription'] or "", key="update_value_desc")
            value_classification = st.selectbox("Company Value Classification", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['CompanyValueClassification']) if demand['CompanyValueClassification'] else 0, key="update_value_class")
            complexity = st.selectbox("Implementation Complexity", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['ImplementationComplexity']) if demand['ImplementationComplexity'] else 0, key="update_complexity")
            cost_estimate = st.selectbox("Implementation Cost Estimate", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['ImplementationCostEstimate']) if demand['ImplementationCostEstimate'] else 0, key="update_cost")
            duration = st.text_input("Implementation Duration", value=demand['ImplementationDuration'] or "", key="update_duration")
            vendor_list = get_dropdown_data("SELECT ID, Description FROM Vendor")
            vendor_options = [f"{d} (ID: {i})" for i, d in vendor_list]
            vendor = st.selectbox("Vendor", ["No vendor selected"] + vendor_options, index=next((i+1 for i, v in enumerate(vendor_list) if v[0] == demand['VendorID']), 0) if demand['VendorID'] else 0, key="update_vendor")
            vendor_id = get_id(vendor) if vendor != "No vendor selected" else None

            if st.button("Update Demand", key="update_submit"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE Demand SET
                            GoLiveDate = %s, AbandonmentReason = %s, CompanyPriority = %s,
                            CompanyValueDescription = %s, CompanyValueClassification = %s,
                            ImplementationComplexity = %s, ImplementationCostEstimate = %s,
                            ImplementationDuration = %s, VendorID = %s
                        WHERE ID = %s
                    """, (
                        go_live_date if demand['Status'] != "Abandoned" else None,
                        abandonment_reason if demand['Status'] == "Abandoned" else None,
                        priority, value_description, value_classification,
                        complexity, cost_estimate, duration, vendor_id, demand_id
                    ))
                    conn.commit()
                    st.success(f"✅ Demand '{selected_demand}' updated successfully.")
                except mysql.connector.Error as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    if conn.is_connected():
                        cursor.close()
                        conn.close()

with tab3:
    st.header("Admin Update - Initial Fields")

    selected_admin_demand = st.selectbox("Select Demand", demand_options, index=0, key="admin_demand")
    if selected_admin_demand != "Select a demand":
        demand_id = get_id(selected_admin_demand)
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Demand WHERE ID = %s", (demand_id,))
            demand = cursor.fetchone()
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            st.error(f"❌ Error fetching demand: {str(e)}")
            demand = None

        if demand:
            name = st.text_input("Demand Name", value=demand['Name'], key="admin_name")
            description = st.text_area("Description", value=demand['Description'], key="admin_description")
            received_date = st.date_input("Received Date", value=demand['ReceivedDate'], key="admin_received_date")
            status = st.selectbox("Status", ["Active", "Paused", "Abandoned"], index=["Active", "Paused", "Abandoned"].index(demand['Status']), key="admin_status")
            phase = st.selectbox("Phase", ["Identify", "Discovery", "Planning", "Delivery", "Live"], index=["Identify", "Discovery", "Planning", "Delivery", "Live"].index(demand['Phase']), key="admin_phase")
            delivery_domain = st.selectbox("Delivery Domain", [
                "Workflow Automation", "Application Modernization", "IOT Driven Digitalization",
                "AI and Machine Learning", "Digital Literacy and Learning",
                "Data Intelligence & Analytics", "Agriculture Process Automation"
            ], index=["Workflow Automation", "Application Modernization", "IOT Driven Digitalization",
                      "AI and Machine Learning", "Digital Literacy and Learning",
                      "Data Intelligence & Analytics", "Agriculture Process Automation"].index(demand['DeliveryDomain']), key="admin_delivery_domain")
            service_category = st.selectbox("Service Category", ["Implementation", "Advisory"], index=["Implementation", "Advisory"].index(demand['ServiceCategory']), key="admin_service_category")
            project_sponsor = st.text_input("Project Sponsor", value=demand['ProjectSponsor'] or "", key="admin_project_sponsor")

            company = st.selectbox("Company", [f"{n} (ID: {i})" for i, n in company_list], index=next((i for i, c in enumerate(company_list) if c[0] == demand['CompanyID']), 0), key="admin_company")
            project_manager = st.selectbox("Project Manager", ["Select a person"] + employee_options, index=next((i+1 for i, e in enumerate(employee_list) if e[0] == demand['ProjectManagerID']), 0), key="admin_pm")
            owner = st.selectbox("Product Owner", ["Select a person"] + employee_options, index=next((i+1 for i, e in enumerate(employee_list) if e[0] == demand['ProductOwnerID']), 0), key="admin_owner")
            dto = st.selectbox("Digital Transformation Owner", ["Select a person"] + employee_options, index=next((i+1 for i, e in enumerate(employee_list) if e[0] == demand['DTOwnerID']), 0), key="admin_dto")

            company_id = get_id(company)
            pm_id = get_id(project_manager)
            owner_id = get_id(owner)
            dto_id = get_id(dto)

            if st.button("Admin Update Demand", key="admin_submit"):
                if "Select a person" in [project_manager, owner, dto] or len({pm_id, owner_id, dto_id}) < 3:
                    st.error("❌ Project Manager, Product Owner, and Digital Transformation Owner must be selected and different.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Demand SET
                                Name = %s, Description = %s, ReceivedDate = %s, Status = %s,
                                Phase = %s, DeliveryDomain = %s, ServiceCategory = %s,
                                CompanyID = %s, ProjectManagerID = %s, ProductOwnerID = %s, DTOwnerID = %s,
                                ProjectSponsor = %s
                            WHERE ID = %s
                        """, (
                            name, description, received_date, status, phase,
                            delivery_domain, service_category, company_id, pm_id, owner_id, dto_id,
                            project_sponsor or None, demand_id
                        ))
                        conn.commit()
                        st.success(f"✅ Demand '{selected_admin_demand}' updated successfully.")
                    except mysql.connector.Error as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        if conn.is_connected():
                            cursor.close()
                            conn.close()